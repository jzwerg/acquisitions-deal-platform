"""Temporal activities.

Determinism boundary (ADR 0004): every LLM / non-deterministic call and every
side effect (DB writes) lives in an activity, never in workflow code. All deal
activities are idempotent (upsert by ``deal_id``) so Temporal's at-least-once
execution is safe. For Milestone 2 the agent steps stay mocked (``LLM_MOCK``);
real matching/outreach arrive in later milestones (see PLAN.md).
"""
from temporalio import activity

from app.config import LLM_MOCK
from app.db import upsert_deal
from app.matching import match_mandate
from worker.shared import Match


@activity.defn
async def stub_agent_activity(prompt: str) -> str:
    """Placeholder agent step; deterministic mock while LLM_MOCK is set."""
    if LLM_MOCK:
        return f"[mock] LLM disabled (LLM_MOCK=true); echoing prompt: {prompt}"
    raise NotImplementedError("Live LLM calls arrive in a later milestone.")


@activity.defn
async def screen_and_match(mandate_id: str) -> list[Match]:
    """Return ranked, explained matches for a mandate (embeddings + re-rank).

    Runs the real hybrid matching pipeline (retrieval + re-rank) inside this
    activity — the determinism boundary (ADR 0004). Falls back to a placeholder
    when the mandate/embeddings aren't present yet (e.g. `make embed` not run),
    so the durability demo still works without seeded data.
    """
    matches = await match_mandate(mandate_id)
    if matches:
        activity.logger.info("matched %d listings for %s", len(matches), mandate_id)
        return matches
    activity.logger.info(
        "no matches for %s (unseeded / no embeddings); using fallback", mandate_id
    )
    return [
        Match("listing-42-0000", "Apex Cloud", 0.5,
              "Fallback match — run `make seed && make embed` for real matching."),
    ]


@activity.defn
async def draft_outreach(deal_id: str, match: Match) -> str:
    """Draft an outreach note. Mocked under LLM_MOCK (no API key needed)."""
    if LLM_MOCK:
        return (
            f"[mock outreach] Introductory note for deal {deal_id} re: "
            f"{match.business_name} — {match.rationale}"
        )
    raise NotImplementedError("Live outreach drafting arrives in Milestone 5.")


@activity.defn
async def persist_deal_state(
    deal_id: str,
    mandate_id: str,
    stage: str,
    top_match_id: str | None = None,
    outreach_draft: str | None = None,
) -> None:
    """Idempotently record a deal's current stage (business record in Postgres)."""
    await upsert_deal(
        deal_id,
        mandate_id=mandate_id,
        stage=stage,
        top_match_id=top_match_id,
        outreach_draft=outreach_draft,
    )


@activity.defn
async def archive_deal(deal_id: str, reason: str) -> None:
    """Idempotently archive a deal (declined / NDA timeout) — clean terminal state."""
    await upsert_deal(
        deal_id, stage="archived", outcome="archived", reason=reason
    )
