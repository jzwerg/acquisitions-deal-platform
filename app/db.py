"""Database access for synthetic data loading.

The schema is owned by ``db/init.sql`` (it declares the pgvector ``embedding``
column, which we deliberately don't touch here). This module defines just the
columns we insert and provides an idempotent upsert keyed on ``id`` — rerunning
``make seed`` with the same seed leaves the same rows, and the ``embedding``
column stays NULL until Milestone 3.
"""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Column, Float, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import create_async_engine

from app import config
from app.models import BuyerMandate, SellerListing

metadata = MetaData()

# Only the columns we write. `embedding` (vector) and `created_at` are owned by
# init.sql with their own defaults and are intentionally absent here.
mandates_table = Table(
    "mandates",
    metadata,
    Column("id", Text, primary_key=True),
    Column("buyer_name", Text, nullable=False),
    Column("sectors", ARRAY(Text), nullable=False),
    Column("regions", ARRAY(Text), nullable=False),
    Column("revenue_min", Float),
    Column("revenue_max", Float),
    Column("target_ebitda_band", Text, nullable=False),
    Column("deal_size_min", Float, nullable=False),
    Column("deal_size_max", Float, nullable=False),
    Column("criteria", Text, nullable=False),
)

listings_table = Table(
    "listings",
    metadata,
    Column("id", Text, primary_key=True),
    Column("business_name", Text, nullable=False),
    Column("sector", Text, nullable=False),
    Column("region", Text, nullable=False),
    Column("revenue", Float, nullable=False),
    Column("ebitda", Float, nullable=False),
    Column("ebitda_band", Text, nullable=False),
    Column("asking_min", Float, nullable=False),
    Column("asking_max", Float, nullable=False),
    Column("description", Text, nullable=False),
)


def async_url(url: str) -> str:
    """Adapt a standard postgres URL to the asyncpg driver SQLAlchemy needs."""
    if url.startswith("postgresql+"):
        return url
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


def _mandate_row(m: BuyerMandate) -> dict:
    return {
        "id": m.id,
        "buyer_name": m.buyer_name,
        "sectors": list(m.sectors),
        "regions": list(m.regions),
        "revenue_min": m.revenue_min,
        "revenue_max": m.revenue_max,
        "target_ebitda_band": m.target_ebitda_band,
        "deal_size_min": m.deal_size_min,
        "deal_size_max": m.deal_size_max,
        "criteria": m.criteria,
    }


def _listing_row(s: SellerListing) -> dict:
    return {
        "id": s.id,
        "business_name": s.business_name,
        "sector": s.sector,
        "region": s.region,
        "revenue": s.revenue,
        "ebitda": s.ebitda,
        "ebitda_band": s.ebitda_band,
        "asking_min": s.asking_min,
        "asking_max": s.asking_max,
        "description": s.description,
    }


def _upsert(table: Table, rows: list[dict]):
    stmt = pg_insert(table).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name] for c in table.columns if c.name != "id"
    }
    return stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)


async def write_all(
    mandates: Sequence[BuyerMandate], listings: Sequence[SellerListing]
) -> None:
    """Upsert mandates and listings into Postgres (idempotent by id)."""
    engine = create_async_engine(async_url(config.DATABASE_URL))
    try:
        async with engine.begin() as conn:
            if mandates:
                await conn.execute(
                    _upsert(mandates_table, [_mandate_row(m) for m in mandates])
                )
            if listings:
                await conn.execute(
                    _upsert(listings_table, [_listing_row(s) for s in listings])
                )
    finally:
        await engine.dispose()
