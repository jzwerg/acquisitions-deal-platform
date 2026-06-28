"""Synthetic generator is deterministic and well-formed (Milestone 1, no DB)."""
from app.models import Region, Sector
from app.seed import generate


def test_generate_counts():
    mandates, listings = generate(seed=42, n_mandates=5, n_listings=12)
    assert len(mandates) == 5
    assert len(listings) == 12


def test_generate_is_deterministic():
    a_m, a_l = generate(seed=42, n_mandates=8, n_listings=20)
    b_m, b_l = generate(seed=42, n_mandates=8, n_listings=20)
    assert [m.model_dump() for m in a_m] == [m.model_dump() for m in b_m]
    assert [s.model_dump() for s in a_l] == [s.model_dump() for s in b_l]


def test_different_seeds_differ():
    a_m, _ = generate(seed=1, n_mandates=8, n_listings=8)
    b_m, _ = generate(seed=2, n_mandates=8, n_listings=8)
    assert [m.model_dump() for m in a_m] != [m.model_dump() for m in b_m]


def test_ids_are_stable_and_unique():
    mandates, listings = generate(seed=7, n_mandates=10, n_listings=30)
    ids = [m.id for m in mandates] + [s.id for s in listings]
    assert len(ids) == len(set(ids))
    assert mandates[0].id == "mandate-7-0000"
    assert listings[0].id == "listing-7-0000"


def test_generated_values_are_valid_enums():
    mandates, listings = generate(seed=3, n_mandates=10, n_listings=30)
    valid_sectors = {s.value for s in Sector}
    valid_regions = {r.value for r in Region}
    for m in mandates:
        assert set(m.sectors) <= valid_sectors
        assert set(m.regions) <= valid_regions
        assert m.deal_size_max >= m.deal_size_min
    for s in listings:
        assert s.sector in valid_sectors
        assert s.region in valid_regions
        assert s.asking_max >= s.asking_min
