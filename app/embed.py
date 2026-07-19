"""Compute + store embeddings for seeded mandates and listings (`make embed`).

Mock-first: uses the deterministic mock backend by default (no API key), so the
pgvector `embedding` columns get populated and retrieval works offline. With
`LLM_MOCK=false` it would use the real embedding provider (see ADR 0002).
"""
from __future__ import annotations

import asyncio

from app import config
from app.db import (
    dispose_engine,
    fetch_listings,
    fetch_mandates,
    set_embedding,
)
from app.embeddings import embed_text, to_pgvector_str
from app.matching import build_listing_text, build_mandate_text


async def _amain() -> None:
    mandates = await fetch_mandates()
    for m in mandates:
        vec = to_pgvector_str(embed_text(build_mandate_text(m)))
        await set_embedding("mandates", m["id"], vec)

    listings = await fetch_listings()
    for listing in listings:
        vec = to_pgvector_str(embed_text(build_listing_text(listing)))
        await set_embedding("listings", listing["id"], vec)

    await dispose_engine()
    backend = "mock" if config.LLM_MOCK else "real"
    print(
        f"Embedded {len(mandates)} mandates and {len(listings)} listings "
        f"(dim={config.EMBEDDING_DIM}, backend={backend})."
    )


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
