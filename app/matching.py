"""Hybrid matching pipeline (ADR 0002): retrieve then re-rank.

1. Embed the mandate, retrieve a shortlist of listings by **structured filter +
   pgvector similarity** (see ``app.db.retrieve_listings``).
2. **Re-rank** the shortlist against the mandate's explicit criteria, attaching a
   **score and a written rationale** per match.

Backend is mock-first (``LLM_MOCK``): the mock re-rank is a deterministic,
explainable scoring blend so the pipeline is real and reproducible with no API
key. The real (LLM) re-rank turns on behind ``LLM_MOCK=false``.
"""
from __future__ import annotations

from app import config
from app.db import fetch_mandate, retrieve_listings
from app.embeddings import embed_text, to_pgvector_str
from worker.shared import Match


def build_mandate_text(m: dict) -> str:
    """Text embedded for a mandate: structured attributes + free-text criteria."""
    return " ".join(
        [
            " ".join(m.get("sectors") or []),
            " ".join(m.get("regions") or []),
            m.get("target_ebitda_band") or "",
            m.get("criteria") or "",
        ]
    ).strip()


def build_listing_text(listing: dict) -> str:
    """Text embedded for a listing: structured attributes + description."""
    return " ".join(
        [
            listing.get("sector") or "",
            listing.get("region") or "",
            listing.get("ebitda_band") or "",
            listing.get("business_name") or "",
            listing.get("description") or "",
        ]
    ).strip()


def _rationale(sim, sector_hit, region_hit, band_hit, size_fit, m, c) -> str:
    bits = []
    bits.append(
        f"Sector match ({c['sector']})" if sector_hit
        else f"Sector {c['sector']} outside mandate"
    )
    bits.append(
        f"region match ({c['region']})" if region_hit
        else f"region {c['region']} outside mandate"
    )
    bits.append(
        f"EBITDA band {c['ebitda_band']} as targeted" if band_hit
        else f"EBITDA band {c['ebitda_band']} vs target {m['target_ebitda_band']}"
    )
    bits.append("asking price within deal size" if size_fit else "asking price outside deal size")
    bits.append(f"semantic similarity {sim:.2f}")
    return "; ".join(bits) + "."


def _mock_rerank(m: dict, candidates: list[dict]) -> list[Match]:
    scored: list[tuple[float, Match]] = []
    for c in candidates:
        sim = float(c.get("similarity") or 0.0)
        sector_hit = c["sector"] in (m.get("sectors") or [])
        region_hit = c["region"] in (m.get("regions") or [])
        band_hit = c["ebitda_band"] == m.get("target_ebitda_band")
        size_fit = (
            c["asking_min"] <= m["deal_size_max"]
            and c["asking_max"] >= m["deal_size_min"]
        )
        score = (
            0.5 * sim
            + 0.20 * sector_hit
            + 0.15 * region_hit
            + 0.10 * band_hit
            + 0.05 * size_fit
        )
        match = Match(
            listing_id=c["id"],
            business_name=c["business_name"],
            score=round(score, 4),
            rationale=_rationale(sim, sector_hit, region_hit, band_hit, size_fit, m, c),
        )
        scored.append((score, match))
    # Deterministic order: score desc, then listing_id for stable ties.
    scored.sort(key=lambda t: (-t[0], t[1].listing_id))
    return [match for _, match in scored]


def _real_rerank(m: dict, candidates: list[dict]) -> list[Match]:
    raise NotImplementedError(
        "Real LLM re-rank turns on with LLM_MOCK=false and a configured "
        "Claude API key (arrives with real agent activities — see PLAN.md)."
    )


def rerank(m: dict, candidates: list[dict]) -> list[Match]:
    if config.LLM_MOCK:
        return _mock_rerank(m, candidates)
    return _real_rerank(m, candidates)


async def match_mandate(
    mandate_id: str, top_n: int = 5, shortlist_n: int = 20
) -> list[Match]:
    """Full pipeline: mandate -> shortlist (retrieve) -> ranked matches (re-rank)."""
    m = await fetch_mandate(mandate_id)
    if m is None:
        return []
    query = to_pgvector_str(embed_text(build_mandate_text(m)))
    candidates = await retrieve_listings(m, query, shortlist_n)
    return rerank(m, candidates)[:top_n]
