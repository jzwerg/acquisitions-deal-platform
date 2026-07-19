"""Mock embedding backend: deterministic, normalized, semantically ordered."""
import math

from app import config
from app.embeddings import embed_text, to_pgvector_str


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def test_dimension_and_determinism():
    v1 = embed_text("saas us software cloud")
    v2 = embed_text("saas us software cloud")
    assert len(v1) == config.EMBEDDING_DIM
    assert v1 == v2  # deterministic


def test_l2_normalized():
    v = embed_text("healthcare uk clinics medical")
    assert abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-6


def test_similar_texts_are_closer():
    a = embed_text("saas us software cloud recurring revenue")
    b = embed_text("saas us software cloud subscription revenue")
    c = embed_text("healthcare uk clinics manufacturing food beverage")
    assert _cos(a, b) > _cos(a, c)


def test_pgvector_str_format():
    s = to_pgvector_str([0.1, -0.2, 0.3])
    assert s.startswith("[") and s.endswith("]")
    assert s.count(",") == 2
