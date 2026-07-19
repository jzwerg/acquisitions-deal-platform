"""FastAPI app — health + the minimal endpoints that drive a deal (Milestone 2).

The API starts deal workflows and relays human-approval signals to Temporal; it
reads deal *state* from Postgres (the business record), keeping Temporal as the
process owner and Postgres as the data owner. Richer endpoints + a UI arrive in
Milestone 6.
"""
import uuid
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import LLM_MOCK, TASK_QUEUE, TEMPORAL_ADDRESS
from app.db import get_deal
from app.matching import match_mandate
from app.temporal_client import get_client
from worker.shared import DealInput
from worker.workflows import DealWorkflow

app = FastAPI(title="Acquisitions Deal Platform API")


@app.get("/health")
def health() -> dict:
    """Liveness check. Returns 200 once the API process is serving."""
    return {
        "status": "ok",
        "llm_mock": LLM_MOCK,
        "temporal_address": TEMPORAL_ADDRESS,
    }


class StartDeal(BaseModel):
    mandate_id: str
    nda_timeout_seconds: int = 30


@app.post("/deals", status_code=201)
async def start_deal(body: StartDeal) -> dict:
    deal_id = f"deal-{uuid.uuid4().hex[:12]}"
    client = await get_client()
    await client.start_workflow(
        DealWorkflow.run,
        DealInput(deal_id, body.mandate_id, body.nda_timeout_seconds),
        id=deal_id,
        task_queue=TASK_QUEUE,
    )
    return {"deal_id": deal_id, "stage": "created"}


async def _signal(deal_id: str, signal) -> dict:
    client = await get_client()
    handle = client.get_workflow_handle(deal_id)
    try:
        await handle.signal(signal)
    except Exception as err:  # noqa: BLE001
        raise HTTPException(
            status_code=404, detail=f"deal {deal_id} not found or not running"
        ) from err
    return {"ok": True, "deal_id": deal_id}


@app.post("/deals/{deal_id}/approve")
async def approve(deal_id: str) -> dict:
    return await _signal(deal_id, DealWorkflow.approve_outreach)


@app.post("/deals/{deal_id}/decline")
async def decline(deal_id: str) -> dict:
    return await _signal(deal_id, DealWorkflow.decline_outreach)


@app.post("/deals/{deal_id}/nda")
async def sign_nda(deal_id: str) -> dict:
    return await _signal(deal_id, DealWorkflow.nda_signed)


@app.get("/deals/{deal_id}")
async def read_deal(deal_id: str) -> dict:
    row = await get_deal(deal_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"deal {deal_id} not found")
    return row


@app.get("/mandates/{mandate_id}/matches")
async def mandate_matches(mandate_id: str, k: int = 5) -> dict:
    """Ranked, explained matches for a mandate (embeddings + re-rank)."""
    matches = await match_mandate(mandate_id, top_n=k)
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"no matches for mandate {mandate_id} (run `make seed && make embed`?)",
        )
    return {"mandate_id": mandate_id, "matches": [asdict(m) for m in matches]}
