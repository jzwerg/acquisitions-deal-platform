"""Domain model validation (Milestone 1)."""
import pytest
from pydantic import ValidationError

from app.models import (
    BuyerMandate,
    EbitdaBand,
    Region,
    SellerListing,
    Sector,
    band_for,
)


def test_band_for_buckets():
    assert band_for(-1) is EbitdaBand.NEGATIVE
    assert band_for(500_000) is EbitdaBand.B0_1M
    assert band_for(3_000_000) is EbitdaBand.B1_5M
    assert band_for(10_000_000) is EbitdaBand.B5_20M
    assert band_for(50_000_000) is EbitdaBand.B20M_PLUS


def test_valid_mandate():
    m = BuyerMandate(
        id="m1",
        buyer_name="Meridian Capital",
        sectors=[Sector.SAAS],
        regions=[Region.UK],
        target_ebitda_band=EbitdaBand.B1_5M,
        deal_size_min=1_000_000,
        deal_size_max=10_000_000,
        criteria="profitable SaaS",
    )
    # use_enum_values stores raw strings, handy for persistence.
    assert m.sectors == ["SaaS"]
    assert m.regions == ["UK"]


def test_mandate_requires_at_least_one_sector_and_region():
    with pytest.raises(ValidationError):
        BuyerMandate(
            id="m2", buyer_name="X", sectors=[], regions=[Region.UK],
            target_ebitda_band=EbitdaBand.B1_5M,
            deal_size_min=1, deal_size_max=2, criteria="c",
        )


def test_mandate_rejects_inverted_deal_size():
    with pytest.raises(ValidationError):
        BuyerMandate(
            id="m3", buyer_name="X", sectors=[Sector.SAAS], regions=[Region.UK],
            target_ebitda_band=EbitdaBand.B1_5M,
            deal_size_min=10, deal_size_max=1, criteria="c",
        )


def test_valid_listing():
    s = SellerListing(
        id="l1",
        business_name="Apex Cloud",
        sector=Sector.SAAS,
        region=Region.US,
        revenue=10_000_000,
        ebitda=2_000_000,
        ebitda_band=EbitdaBand.B1_5M,
        asking_min=8_000_000,
        asking_max=10_000_000,
        description="A SaaS business",
    )
    assert s.sector == "SaaS"


def test_listing_rejects_inconsistent_band():
    with pytest.raises(ValidationError):
        SellerListing(
            id="l2", business_name="X", sector=Sector.SAAS, region=Region.US,
            revenue=10_000_000, ebitda=2_000_000,
            ebitda_band=EbitdaBand.B20M_PLUS,  # wrong band for 2M
            asking_min=1, asking_max=2, description="d",
        )
