"""Minimal FastAPI app for Milestone 0.

Exposes a single health endpoint so `docker compose up` can be smoke-checked
(`curl localhost:8000/health` -> 200). Deal/match endpoints arrive later
(see PLAN.md).
"""
from fastapi import FastAPI

from app.config import LLM_MOCK, TEMPORAL_ADDRESS

app = FastAPI(title="Acquisitions Deal Platform API")


@app.get("/health")
def health() -> dict:
    """Liveness check. Returns 200 once the API process is serving."""
    return {
        "status": "ok",
        "llm_mock": LLM_MOCK,
        "temporal_address": TEMPORAL_ADDRESS,
    }
