"""Durability + determinism tests for DealWorkflow.

Runs the workflow in Temporal's **time-skipping** test environment with mocked
activities (no DB, no API key), exercising all three terminal paths, then
**replays** the recorded history to prove the workflow is deterministic — the
guarantee that lets a killed worker resume exactly where it left off.

The time-skipping test server is fetched on first use. Where that download is
unavailable (e.g. an offline Claude Code web session) these tests **skip**;
they run for real in CI, which is where the durability proof lives.
"""
import asyncio
import uuid

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

from worker.shared import DealInput, Match
from worker.workflows import DealWorkflow

TASK_QUEUE = "test-deals"


# --- mocked activities, matched to the real ones by name (no DB) ---
@activity.defn(name="screen_and_match")
async def mock_screen(mandate_id: str) -> list[Match]:
    return [Match("listing-x", "Mock Biz", 0.9, "sector + size fit")]


@activity.defn(name="draft_outreach")
async def mock_draft(deal_id: str, match: Match) -> str:
    return "mock outreach draft"


@activity.defn(name="persist_deal_state")
async def mock_persist(
    deal_id: str, mandate_id: str, stage: str,
    top_match_id: str | None = None, outreach_draft: str | None = None,
) -> None:
    return None


@activity.defn(name="archive_deal")
async def mock_archive(deal_id: str, reason: str) -> None:
    return None


MOCK_ACTIVITIES = [mock_screen, mock_draft, mock_persist, mock_archive]


async def _start_env() -> WorkflowEnvironment:
    try:
        return await WorkflowEnvironment.start_time_skipping()
    except Exception as ex:  # noqa: BLE001 - offline sandbox can't fetch the server
        pytest.skip(f"Temporal test server unavailable: {ex}")


def _deal_id() -> str:
    return f"deal-{uuid.uuid4().hex[:8]}"


async def _run(signals, nda_timeout=300):
    """Start a deal, apply signals, return (result, history)."""
    env = await _start_env()
    try:
        async with Worker(
            env.client, task_queue=TASK_QUEUE,
            workflows=[DealWorkflow], activities=MOCK_ACTIVITIES,
        ):
            deal_id = _deal_id()
            handle = await env.client.start_workflow(
                DealWorkflow.run,
                DealInput(deal_id, "mandate-x", nda_timeout),
                id=deal_id, task_queue=TASK_QUEUE,
            )
            # Signals are buffered by the server; the workflow applies them when
            # it reaches each wait — so no polling is needed.
            for sig in signals:
                await handle.signal(sig)
            result = await handle.result()
            history = await handle.fetch_history()
            return result, history
    finally:
        await env.shutdown()


def test_happy_path_closes_and_replays_deterministically():
    async def go():
        result, history = await _run(
            [DealWorkflow.approve_outreach, DealWorkflow.nda_signed]
        )
        assert result.outcome == "closed"
        assert result.reason == "completed"
        # Determinism: replaying the recorded history must not raise.
        await Replayer(workflows=[DealWorkflow]).replay_workflow(history)

    asyncio.run(go())


def test_decline_archives():
    async def go():
        result, _ = await _run([DealWorkflow.decline_outreach])
        assert result.outcome == "archived"
        assert result.reason == "declined"

    asyncio.run(go())


def test_nda_timeout_archives():
    async def go():
        # Approve but never sign the NDA; time-skipping fires the durable timer.
        result, _ = await _run([DealWorkflow.approve_outreach], nda_timeout=5)
        assert result.outcome == "archived"
        assert result.reason == "nda_timeout"

    asyncio.run(go())
