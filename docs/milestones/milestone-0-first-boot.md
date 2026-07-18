# Milestone 0 — First `docker compose up`

The single goal of this milestone: **`make up` brings Temporal, a long-running
worker, Postgres, and the API to a healthy state** — with the LLM mocked so no API
key is needed. This is *not* the kill-a-worker demo or real matching (those come
later). Keep scope tight.

## Definition of done
- `cp .env.example .env && make up` boots Postgres (pgvector), Temporal (+ UI), the
  `api`, and the `worker`. `LLM_MOCK=true` means no `ANTHROPIC_API_KEY` is required.
- `api` builds (needs a **Python Dockerfile**) and serves a health endpoint on
  **:8000**; `worker` uses the same image and **connects to Temporal and starts
  polling** a task queue.
- `make down` tears everything down cleanly.

## Smoke check (how you know it worked)
- `curl -fsS localhost:8000/health` → `200`.
- Temporal UI loads at `http://localhost:8001`.
- `worker` logs show it started polling its task queue (no connection errors).

## Explicitly out of scope (later milestones)
Real embeddings/LLM matching, the deal-lifecycle workflow, approval-gate signals,
the kill-a-worker durability demo, the precision@k eval. See `PLAN.md`.

## Stack gotchas
- The **worker is a separate long-running service**, not a serverless function —
  that's the whole point. It shares the API image, different entrypoint.
- `temporalio/auto-setup` takes ~20–30s before it accepts connections; the worker
  must **retry** connecting rather than crash on first failure.
- Keep the determinism boundary in mind for later: all LLM/non-deterministic calls
  live in **activities**, never in workflow code (see `docs/adr/0004...`).
- Pin images as in compose (`temporalio/auto-setup:1.25.2`, `pgvector:pg16`); use
  Python `3.12` to match CI.

## Shared conventions (portfolio-wide — keep identical across all four repos)
- **Branch:** `claude/product-thinking-repos-cmbegm`.
- **Task interface:** `make up` / `down` / `demo` / `test` / `logs`.
- **First boot needs no secrets** — `.env.example` defaults must boot (LLM mocked).
- **Compose v2:** `docker compose` (space), not the deprecated `docker-compose`.
- **Host ports:** this project owns the **80xx** range.
- **Validate without a daemon:** `docker compose config -q` parses the stack even
  where Docker can't run (e.g. a Claude Code web session); a real boot must be
  verified on a machine with a Docker daemon.

## Paste-ready session kickoff
> Get this repo to its first `docker compose up` state per `MILESTONE.md`. Add a
> Python Dockerfile, a minimal FastAPI app with `/health`, and a Temporal worker
> entrypoint that connects and polls a task queue with retry. Keep `LLM_MOCK=true`
> so it boots with no API key. Don't build the deal workflow, real matching, or the
> kill-a-worker demo yet. Validate with `docker compose config -q`, then confirm the
> smoke check. Commit to `claude/product-thinking-repos-cmbegm` and push.
