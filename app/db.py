"""Database access for synthetic data + deal state.

The schema is owned by ``db/init.sql``. Profiles (mandates/listings) and deal
state both live in Postgres — Temporal owns the *process*, Postgres owns the
*data* (see PLAN.md). Deal writes are idempotent (upsert by ``deal_id``) so
Temporal's at-least-once activity execution never corrupts state.
"""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import (
    Column,
    Float,
    MetaData,
    Table,
    Text,
    bindparam,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

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

deals_table = Table(
    "deals",
    metadata,
    Column("deal_id", Text, primary_key=True),
    Column("mandate_id", Text),
    Column("stage", Text, nullable=False),
    Column("outcome", Text),
    Column("reason", Text),
    Column("top_match_id", Text),
    Column("outreach_draft", Text),
)

_engine: AsyncEngine | None = None


def async_url(url: str) -> str:
    """Adapt a standard postgres URL to the asyncpg driver SQLAlchemy needs."""
    if url.startswith("postgresql+"):
        return url
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


def get_engine() -> AsyncEngine:
    """Lazily create and cache one async engine per process/event loop."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(async_url(config.DATABASE_URL))
    return _engine


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


# --- synthetic data (make seed) --------------------------------------------


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


def _upsert(table: Table, rows: list[dict], key: str):
    stmt = pg_insert(table).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name] for c in table.columns if c.name != key
    }
    return stmt.on_conflict_do_update(index_elements=[key], set_=update_cols)


async def write_all(
    mandates: Sequence[BuyerMandate], listings: Sequence[SellerListing]
) -> None:
    """Upsert mandates and listings into Postgres (idempotent by id)."""
    engine = get_engine()
    async with engine.begin() as conn:
        if mandates:
            await conn.execute(
                _upsert(mandates_table, [_mandate_row(m) for m in mandates], "id")
            )
        if listings:
            await conn.execute(
                _upsert(listings_table, [_listing_row(s) for s in listings], "id")
            )


# --- deal state (Temporal activities) --------------------------------------


async def upsert_deal(deal_id: str, **fields) -> None:
    """Upsert a deal row, updating only the provided (non-None) columns.

    Idempotent by ``deal_id`` — safe under Temporal's at-least-once activity
    execution and never clobbers an existing column with NULL.
    """
    values = {"deal_id": deal_id}
    values.update({k: v for k, v in fields.items() if v is not None})
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(_upsert(deals_table, [values], "deal_id"))


async def get_deal(deal_id: str) -> dict | None:
    engine = get_engine()
    async with engine.connect() as conn:
        res = await conn.execute(
            select(deals_table).where(deals_table.c.deal_id == deal_id)
        )
        row = res.mappings().first()
    return dict(row) if row else None


# --- matching (embeddings + retrieval) -------------------------------------


async def fetch_mandate(mandate_id: str) -> dict | None:
    engine = get_engine()
    async with engine.connect() as conn:
        res = await conn.execute(
            select(mandates_table).where(mandates_table.c.id == mandate_id)
        )
        row = res.mappings().first()
    return dict(row) if row else None


async def fetch_mandates() -> list[dict]:
    engine = get_engine()
    async with engine.connect() as conn:
        res = await conn.execute(select(mandates_table))
        return [dict(r) for r in res.mappings().all()]


async def fetch_listings() -> list[dict]:
    engine = get_engine()
    async with engine.connect() as conn:
        res = await conn.execute(select(listings_table))
        return [dict(r) for r in res.mappings().all()]


async def set_embedding(table_name: str, row_id: str, vector_str: str) -> None:
    """Write a pgvector embedding to a row. ``table_name`` is caller-controlled
    (``mandates``/``listings``), never user input."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                f"UPDATE {table_name} SET embedding = CAST(:emb AS vector) "
                "WHERE id = :id"
            ),
            {"emb": vector_str, "id": row_id},
        )


_LISTING_COLS = (
    "id, business_name, sector, region, revenue, ebitda, ebitda_band, "
    "asking_min, asking_max, description"
)


async def retrieve_listings(
    mandate: dict, query_vector_str: str, top_n: int
) -> list[dict]:
    """Structured pre-filter + pgvector cosine similarity (ADR 0002).

    Returns the top-N most similar listings; falls back to pure vector search if
    the structured filter yields nothing.
    """
    engine = get_engine()
    sim = "1 - (embedding <=> CAST(:q AS vector)) AS similarity"
    order = "embedding <=> CAST(:q AS vector)"
    params = {
        "q": query_vector_str,
        "sectors": mandate["sectors"],
        "regions": mandate["regions"],
        "dmin": mandate["deal_size_min"],
        "dmax": mandate["deal_size_max"],
        "n": top_n,
    }
    strict = (
        text(
            f"SELECT {_LISTING_COLS}, {sim} FROM listings "
            "WHERE embedding IS NOT NULL "
            "AND sector = ANY(:sectors) AND region = ANY(:regions) "
            "AND asking_min <= :dmax AND asking_max >= :dmin "
            f"ORDER BY {order} LIMIT :n"
        ).bindparams(
            bindparam("sectors", type_=ARRAY(Text)),
            bindparam("regions", type_=ARRAY(Text)),
        )
    )
    loose = text(
        f"SELECT {_LISTING_COLS}, {sim} FROM listings "
        f"WHERE embedding IS NOT NULL ORDER BY {order} LIMIT :n"
    )
    async with engine.connect() as conn:
        res = await conn.execute(strict, params)
        rows = [dict(r) for r in res.mappings().all()]
        if not rows:
            res = await conn.execute(loose, params)
            rows = [dict(r) for r in res.mappings().all()]
    return rows
