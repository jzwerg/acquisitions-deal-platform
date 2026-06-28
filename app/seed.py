"""Seeded synthetic data generator (`make seed`).

Produces realistic, regionally-varied buyer mandates and seller listings. The
core ``generate(...)`` is **pure and deterministic** (seeded RNG, no DB, no
wall-clock) so the Milestone 4 eval and the tests are reproducible; ``main()`` is
the thin layer that writes the result to Postgres.
"""
from __future__ import annotations

import asyncio
import random

from app import config
from app.db import write_all
from app.models import (
    BuyerMandate,
    EbitdaBand,
    Region,
    SellerListing,
    Sector,
    band_for,
)

# Per-region flavor: currency label (for text) and lower-middle-market deal-size
# range in USD-equivalent (kept comparable across regions for matching).
REGIONS: dict[Region, dict] = {
    Region.UK: {"currency": "GBP", "size": (1_000_000, 30_000_000)},
    Region.EU: {"currency": "EUR", "size": (1_000_000, 50_000_000)},
    Region.US: {"currency": "USD", "size": (2_000_000, 75_000_000)},
    Region.SG: {"currency": "SGD", "size": (1_000_000, 40_000_000)},
}

SECTORS = list(Sector)

_BUYER_PREFIXES = [
    "Meridian", "Ashgrove", "Northbridge", "Kestrel", "Lionheart", "Cedarpoint",
    "Brightwater", "Stonecourt", "Harborview", "Silverpine",
]
_BUYER_TYPES = ["Capital", "Partners", "Equity", "Holdings", "Search Fund"]

_BIZ_ADJ = [
    "Apex", "Vertex", "Summit", "Clearpath", "Truenorth", "Ironclad",
    "Beacon", "Catalyst", "Evergreen", "Quantum", "Pioneer", "Keystone",
]
_BIZ_NOUN = {
    Sector.SAAS: ["Systems", "Cloud", "Labs", "Software"],
    Sector.HEALTHCARE: ["Health", "Care", "Clinics", "Medical"],
    Sector.MANUFACTURING: ["Industries", "Manufacturing", "Works", "Fabrication"],
    Sector.LOGISTICS: ["Logistics", "Freight", "Distribution", "Supply"],
    Sector.FINTECH: ["Pay", "Finance", "Capital Tech", "Ledger"],
    Sector.CONSUMER: ["Brands", "Goods", "Products", "Consumer"],
    Sector.PROFESSIONAL_SERVICES: ["Advisory", "Consulting", "Partners", "Group"],
    Sector.FOOD_BEVERAGE: ["Foods", "Beverages", "Kitchens", "Provisions"],
    Sector.ECOMMERCE: ["Commerce", "Retail", "Marketplace", "Direct"],
    Sector.BUSINESS_SERVICES: ["Services", "Solutions", "Group", "Operations"],
}


def _money(rng: random.Random, low: float, high: float) -> float:
    """A rounded amount in [low, high]."""
    return float(round(rng.uniform(low, high), -3))


def _make_mandate(rng: random.Random, i: int, seed: int) -> BuyerMandate:
    sectors = rng.sample(SECTORS, k=rng.randint(1, 3))
    regions = rng.sample(list(REGIONS), k=rng.randint(1, 2))
    # Deal size spans the chosen regions' ranges.
    lo = min(REGIONS[r]["size"][0] for r in regions)
    hi = max(REGIONS[r]["size"][1] for r in regions)
    size_min = _money(rng, lo, (lo + hi) / 2)
    size_max = _money(rng, size_min, hi)
    band = rng.choice(
        [b for b in EbitdaBand if b is not EbitdaBand.NEGATIVE]
    )
    sector_text = ", ".join(s.value for s in sectors)
    region_text = "/".join(r.value for r in regions)
    return BuyerMandate(
        id=f"mandate-{seed}-{i:04d}",
        buyer_name=f"{rng.choice(_BUYER_PREFIXES)} {rng.choice(_BUYER_TYPES)}",
        sectors=sectors,
        regions=regions,
        revenue_min=_money(rng, size_min * 0.5, size_min),
        revenue_max=_money(rng, size_max, size_max * 2),
        target_ebitda_band=band,
        deal_size_min=size_min,
        deal_size_max=size_max,
        criteria=(
            f"Seeking profitable {sector_text} businesses in {region_text} with "
            f"EBITDA in the {band.value} band; founder-led, recurring revenue and "
            f"a clear path to operational improvement preferred."
        ),
    )


def _make_listing(rng: random.Random, i: int, seed: int) -> SellerListing:
    sector = rng.choice(SECTORS)
    region = rng.choice(list(REGIONS))
    currency = REGIONS[region]["currency"]
    revenue = _money(rng, 2_000_000, 60_000_000)
    # Mostly profitable; a small share distressed (negative EBITDA).
    margin = rng.uniform(0.05, 0.30) if rng.random() > 0.1 else rng.uniform(-0.10, 0.0)
    ebitda = float(round(revenue * margin, -3))
    multiple = rng.uniform(4.0, 10.0)
    asking_mid = max(ebitda, revenue * 0.2) * multiple
    asking_min = _money(rng, asking_mid * 0.85, asking_mid)
    asking_max = _money(rng, asking_mid, asking_mid * 1.15)
    name = f"{rng.choice(_BIZ_ADJ)} {rng.choice(_BIZ_NOUN[sector])}"
    return SellerListing(
        id=f"listing-{seed}-{i:04d}",
        business_name=name,
        sector=sector,
        region=region,
        revenue=revenue,
        ebitda=ebitda,
        ebitda_band=band_for(ebitda),
        asking_min=asking_min,
        asking_max=asking_max,
        description=(
            f"{name} is a {region.value}-based {sector.value} business with "
            f"~{currency} {revenue:,.0f} revenue and {currency} {ebitda:,.0f} "
            f"EBITDA. Owner seeking exit; stable customer base and experienced "
            f"management team in place."
        ),
    )


def generate(
    seed: int, n_mandates: int, n_listings: int
) -> tuple[list[BuyerMandate], list[SellerListing]]:
    """Deterministically generate mandates and listings for a given seed."""
    rng = random.Random(seed)
    mandates = [_make_mandate(rng, i, seed) for i in range(n_mandates)]
    listings = [_make_listing(rng, i, seed) for i in range(n_listings)]
    return mandates, listings


async def _amain() -> None:
    mandates, listings = generate(
        config.SEED, config.SEED_MANDATES, config.SEED_LISTINGS
    )
    await write_all(mandates, listings)
    print(
        f"Seeded {len(mandates)} mandates and {len(listings)} listings "
        f"(seed={config.SEED})."
    )


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
