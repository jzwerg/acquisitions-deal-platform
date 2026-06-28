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

# App database (pgvector). Unused at Milestone 0 but wired through for later.
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
