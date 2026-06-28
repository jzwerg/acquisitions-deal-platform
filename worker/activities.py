"""Stubbed agent activities.

Determinism boundary (ADR 0004): every LLM / non-deterministic call lives in a
Temporal *activity*, never in workflow code. For Milestone 0 these stay mocked
(`LLM_MOCK=true`) so the stack boots with no API key. Real screening / matching
/ outreach activities arrive in later milestones (see PLAN.md).
"""
from temporalio import activity

from app.config import LLM_MOCK


@activity.defn
async def stub_agent_activity(prompt: str) -> str:
    """Placeholder agent step.

    Returns a deterministic mock while ``LLM_MOCK`` is set so first boot needs
    no API key. The real LLM call will live here too — inside the activity, so
    the determinism boundary holds.
    """
    if LLM_MOCK:
        return f"[mock] LLM disabled (LLM_MOCK=true); echoing prompt: {prompt}"
    raise NotImplementedError("Live LLM calls arrive in a later milestone.")
