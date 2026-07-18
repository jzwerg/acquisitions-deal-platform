"""Workflow/activity data contracts.

Plain dataclasses only (no heavy imports) so this is safe to import inside the
Temporal workflow sandbox. Serialized by Temporal's default data converter.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DealInput:
    """Input to a deal-lifecycle workflow."""

    deal_id: str
    mandate_id: str
    # NDA wait before the deal is archived on timeout. Passed in (not read from
    # env) so it's recorded in history and stays deterministic on replay.
    nda_timeout_seconds: int = 30


@dataclass
class Match:
    """A ranked buyer<->seller match. Canned in M2; real matching in M3."""

    listing_id: str
    business_name: str
    score: float
    rationale: str


@dataclass
class DealResult:
    """Terminal result of a deal workflow."""

    deal_id: str
    outcome: str  # "closed" | "archived"
    reason: str  # "completed" | "declined" | "nda_timeout"
    top_match_id: str | None = None
