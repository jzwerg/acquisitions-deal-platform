"""Domain models — buyer mandates and seller listings.

Pydantic v2. Structured attributes (sector, region, revenue/EBITDA, deal size)
plus the free text the matching layer (Milestone 3) will embed and reason over.
No persistence concerns here; the DB schema lives in ``db/init.sql``.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Region(str, Enum):
    UK = "UK"
    EU = "EU"
    US = "US"
    SG = "SG"


class Sector(str, Enum):
    SAAS = "SaaS"
    HEALTHCARE = "Healthcare Services"
    MANUFACTURING = "Industrial Manufacturing"
    LOGISTICS = "Logistics & Distribution"
    FINTECH = "FinTech"
    CONSUMER = "Consumer Products"
    PROFESSIONAL_SERVICES = "Professional Services"
    FOOD_BEVERAGE = "Food & Beverage"
    ECOMMERCE = "E-commerce"
    BUSINESS_SERVICES = "Business Services"


class EbitdaBand(str, Enum):
    NEGATIVE = "negative"
    B0_1M = "0-1M"
    B1_5M = "1-5M"
    B5_20M = "5-20M"
    B20M_PLUS = "20M+"


def band_for(ebitda: float) -> EbitdaBand:
    """Bucket an EBITDA figure (USD-equivalent) into a band."""
    if ebitda < 0:
        return EbitdaBand.NEGATIVE
    if ebitda < 1_000_000:
        return EbitdaBand.B0_1M
    if ebitda < 5_000_000:
        return EbitdaBand.B1_5M
    if ebitda < 20_000_000:
        return EbitdaBand.B5_20M
    return EbitdaBand.B20M_PLUS


class BuyerMandate(BaseModel):
    """A buyer's acquisition mandate — what they want to buy."""

    model_config = ConfigDict(use_enum_values=True)

    id: str
    buyer_name: str
    sectors: list[Sector] = Field(min_length=1)
    regions: list[Region] = Field(min_length=1)
    revenue_min: float | None = Field(default=None, ge=0)
    revenue_max: float | None = Field(default=None, ge=0)
    target_ebitda_band: EbitdaBand
    deal_size_min: float = Field(ge=0)
    deal_size_max: float = Field(ge=0)
    criteria: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_ranges(self) -> "BuyerMandate":
        if self.deal_size_max < self.deal_size_min:
            raise ValueError("deal_size_max must be >= deal_size_min")
        if (
            self.revenue_min is not None
            and self.revenue_max is not None
            and self.revenue_max < self.revenue_min
        ):
            raise ValueError("revenue_max must be >= revenue_min")
        return self


class SellerListing(BaseModel):
    """A business for sale — what a seller is offering."""

    model_config = ConfigDict(use_enum_values=True)

    id: str
    business_name: str
    sector: Sector
    region: Region
    revenue: float = Field(ge=0)
    ebitda: float
    ebitda_band: EbitdaBand
    asking_min: float = Field(ge=0)
    asking_max: float = Field(ge=0)
    description: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_consistency(self) -> "SellerListing":
        if self.asking_max < self.asking_min:
            raise ValueError("asking_max must be >= asking_min")
        expected = band_for(self.ebitda)
        # use_enum_values stores the raw string, so compare against .value.
        if self.ebitda_band != expected.value:
            raise ValueError(
                f"ebitda_band {self.ebitda_band!r} inconsistent with ebitda "
                f"{self.ebitda} (expected {expected.value!r})"
            )
        return self
