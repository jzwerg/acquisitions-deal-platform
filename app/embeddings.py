"""Embedding provider abstraction.

Backend is selected by ``LLM_MOCK`` (ADR 0002 leaves the real model open):

- **mock** (default, no network, no key): a deterministic feature-hashing
  ("hashing trick") embedding. Texts that share tokens land closer in cosine
  space, so retrieval is meaningful and reproducible — and the M4 eval gets a
  stable number.
- **real** (only when ``LLM_MOCK=false``): a configured embedding provider
  (Anthropic has no embeddings API, so this is Voyage/OpenAI/local — a
  deliberate later choice). Kept out of the first-boot path.

Determinism boundary (ADR 0004): this is called only from within activities.
"""
from __future__ import annotations

import hashlib
import math
import re

from app import config

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 1]


def _mock_embed(text: str, dim: int) -> list[float]:
    """Deterministic signed feature-hashing embedding, L2-normalized."""
    vec = [0.0] * dim
    for tok in _tokens(text):
        h = int.from_bytes(hashlib.md5(tok.encode()).digest()[:8], "big")
        vec[h % dim] += 1.0 if (h >> 63) & 1 else -1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _real_embed(text: str) -> list[float]:
    raise NotImplementedError(
        "Real embeddings require configuring an embedding provider "
        "(Voyage / OpenAI / local — see ADR 0002). Keep LLM_MOCK=true for now."
    )


def embed_text(text: str) -> list[float]:
    if config.LLM_MOCK:
        return _mock_embed(text, config.EMBEDDING_DIM)
    return _real_embed(text)


def to_pgvector_str(vec: list[float]) -> str:
    """Serialize a vector to pgvector's text input format: ``[a,b,c]``."""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
