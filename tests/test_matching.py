"""Re-rank logic: explainable, deterministic, structured-fit aware (no DB)."""
import asyncio

from app.matching import build_listing_text, build_mandate_text, match_mandate, rerank

MANDATE = {
    "id": "m1",
    "sectors": ["SaaS"],
    "regions": ["US"],
    "target_ebitda_band": "1-5M",
    "deal_size_min": 1_000_000,
    "deal_size_max": 20_000_000,
    "criteria": "profitable saas businesses",
}


def _cand(cid, sector, region, band, sim, amin=5_000_000, amax=8_000_000, name="Biz"):
    return {
        "id": cid, "business_name": name, "sector": sector, "region": region,
        "ebitda_band": band, "asking_min": amin, "asking_max": amax,
        "revenue": 1.0, "ebitda": 1.0, "description": "desc", "similarity": sim,
    }


def test_structured_fit_beats_raw_similarity():
    cands = [
        _cand("good", "SaaS", "US", "1-5M", 0.60),           # full structured fit
        _cand("weak", "Healthcare Services", "UK", "20M+", 0.90),  # high sim only
    ]
    ranked = rerank(MANDATE, cands)
    assert ranked[0].listing_id == "good"
    assert "Sector match" in ranked[0].rationale
    assert "semantic similarity" in ranked[0].rationale


def test_rerank_is_deterministic_with_stable_tiebreak():
    cands = [
        _cand("b", "SaaS", "US", "1-5M", 0.5),
        _cand("a", "SaaS", "US", "1-5M", 0.5),
    ]
    order1 = [m.listing_id for m in rerank(MANDATE, cands)]
    order2 = [m.listing_id for m in rerank(MANDATE, cands)]
    assert order1 == order2 == ["a", "b"]  # equal scores -> id tiebreak


def test_scores_are_bounded_and_rounded():
    ranked = rerank(MANDATE, [_cand("x", "SaaS", "US", "1-5M", 1.0)])
    assert 0.0 <= ranked[0].score <= 1.0


def test_build_texts_include_structured_attrs():
    assert "SaaS" in build_mandate_text(MANDATE)
    assert "US" in build_mandate_text(MANDATE)
    listing = _cand("x", "SaaS", "US", "1-5M", 0.5)
    assert "SaaS" in build_listing_text(listing)


def test_match_mandate_pipeline_composes(monkeypatch):
    """embed -> retrieve -> re-rank wiring, without a database."""
    async def fake_fetch(_mid):
        return MANDATE

    async def fake_retrieve(_m, query, _n):
        assert isinstance(query, str) and query.startswith("[")  # embedded + serialized
        return [
            _cand("good", "SaaS", "US", "1-5M", 0.60),
            _cand("weak", "Healthcare Services", "UK", "20M+", 0.90),
        ]

    monkeypatch.setattr("app.matching.fetch_mandate", fake_fetch)
    monkeypatch.setattr("app.matching.retrieve_listings", fake_retrieve)

    result = asyncio.run(match_mandate("m1", top_n=2))
    assert [m.listing_id for m in result] == ["good", "weak"]
    assert all(m.rationale for m in result)


def test_match_mandate_returns_empty_for_unknown_mandate(monkeypatch):
    async def fake_fetch(_mid):
        return None

    monkeypatch.setattr("app.matching.fetch_mandate", fake_fetch)
    assert asyncio.run(match_mandate("nope")) == []
