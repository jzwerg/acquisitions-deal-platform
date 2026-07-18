"""The deal-lifecycle workflow — deterministic orchestration.

Determinism boundary (ADR 0004): this file contains NO IO, LLM, clock, or
randomness. Everything non-deterministic is an activity; waits use Temporal
signals and durable timers. That's what lets a killed worker resume this
workflow exactly where it left off.

Milestone 2 lifecycle:

    screen & match -> outreach draft -> [approve | decline] ->
        approve  -> await NDA (durable timer) -> [signed -> close | timeout -> archive]
        decline  -> archive

Real matching (M3), the eval (M4), and real agent activities (M5) slot in behind
the activity boundary without changing this workflow.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from worker.activities import (
        archive_deal,
        draft_outreach,
        persist_deal_state,
        screen_and_match,
    )
    from worker.shared import DealInput, DealResult

_ACT_TIMEOUT = timedelta(seconds=30)
_RETRY = RetryPolicy(maximum_attempts=5, initial_interval=timedelta(seconds=1))


@workflow.defn
class DealWorkflow:
    def __init__(self) -> None:
        self._decision: str | None = None  # None | "approved" | "declined"
        self._nda_signed: bool = False
        self._stage: str = "created"

    # --- signals (human-in-the-loop) ---
    @workflow.signal
    def approve_outreach(self) -> None:
        if self._decision is None:
            self._decision = "approved"

    @workflow.signal
    def decline_outreach(self) -> None:
        if self._decision is None:
            self._decision = "declined"

    @workflow.signal
    def nda_signed(self) -> None:
        self._nda_signed = True

    # --- query ---
    @workflow.query
    def stage(self) -> str:
        return self._stage

    async def _persist(self, deal: DealInput, stage: str, top_match_id: str,
                       draft: str | None = None) -> None:
        self._stage = stage
        await workflow.execute_activity(
            persist_deal_state,
            args=[deal.deal_id, deal.mandate_id, stage, top_match_id, draft],
            start_to_close_timeout=_ACT_TIMEOUT,
            retry_policy=_RETRY,
        )

    @workflow.run
    async def run(self, deal: DealInput) -> DealResult:
        matches = await workflow.execute_activity(
            screen_and_match,
            deal.mandate_id,
            start_to_close_timeout=_ACT_TIMEOUT,
            retry_policy=_RETRY,
        )
        top = matches[0]
        await self._persist(deal, "screened", top.listing_id)

        draft = await workflow.execute_activity(
            draft_outreach,
            args=[deal.deal_id, top],
            start_to_close_timeout=_ACT_TIMEOUT,
            retry_policy=_RETRY,
        )
        await self._persist(deal, "awaiting_approval", top.listing_id, draft)

        # Human approval gate — waits durably (possibly for weeks).
        await workflow.wait_condition(lambda: self._decision is not None)
        if self._decision == "declined":
            await workflow.execute_activity(
                archive_deal,
                args=[deal.deal_id, "declined"],
                start_to_close_timeout=_ACT_TIMEOUT,
                retry_policy=_RETRY,
            )
            self._stage = "archived"
            return DealResult(deal.deal_id, "archived", "declined", top.listing_id)

        # Approved: await NDA signature with a durable timer.
        await self._persist(deal, "awaiting_nda", top.listing_id)
        try:
            await workflow.wait_condition(
                lambda: self._nda_signed,
                timeout=timedelta(seconds=deal.nda_timeout_seconds),
            )
        except asyncio.TimeoutError:
            await workflow.execute_activity(
                archive_deal,
                args=[deal.deal_id, "nda_timeout"],
                start_to_close_timeout=_ACT_TIMEOUT,
                retry_policy=_RETRY,
            )
            self._stage = "archived"
            return DealResult(deal.deal_id, "archived", "nda_timeout", top.listing_id)

        await self._persist(deal, "closed", top.listing_id)
        return DealResult(deal.deal_id, "closed", "completed", top.listing_id)
