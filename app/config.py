"""Runtime configuration, read from the environment.

Shared by both the `api` and `worker` services. First boot needs no secrets:
`LLM_MOCK` defaults to true so agent activities stay stubbed and no
`ANTHROPIC_API_KEY` is required (see MILESTONE.md).
"""
import os


def _as_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


# Where the worker (and later the API) reaches the Temporal frontend.
TEMPORAL_ADDRESS: str = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")

# The task queue the worker polls. Workflows/activities land in later milestones.
TASK_QUEUE: str = os.getenv("TASK_QUEUE", "deals-task-queue")

# Mock the LLM so first boot needs no API key. Real matching is a later milestone.
LLM_MOCK: bool = _as_bool(os.getenv("LLM_MOCK", "true"))

# App database (pgvector).
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# Embedding dimension reserved on the `embedding` column. Stays NULL until
# Milestone 3 populates it; the real model choice (ADR 0002) may revise this.
# Keep this in sync with `db/init.sql`.
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1024"))

# Synthetic data generation (`make seed`). Deterministic by SEED.
SEED: int = int(os.getenv("SEED", "42"))
SEED_MANDATES: int = int(os.getenv("SEED_MANDATES", "20"))
SEED_LISTINGS: int = int(os.getenv("SEED_LISTINGS", "100"))
