# Milestone 2 — Durable deal-lifecycle workflow (kill-a-worker demo)

The single goal of this milestone: **the headline durability proof.** A minimal
but real Temporal deal-lifecycle workflow with idempotent, *mocked* activities —
kill the worker mid-deal and it resumes exactly-once; a declined outreach or an
NDA timeout archives the deal cleanly with no orphaned state. Determinism is
proven by a workflow-replay test in CI. Still mock-first (no API key).

> Prerequisite: Milestone 1 (domain & data). The workflow's first activity
> consumes mandates/listings from M1; matching stays **canned/stubbed** here and
> the real matcher plugs in behind the same activity boundary in Milestone 3.

## Definition of done
- **`DealWorkflow`** (in `worker/workflows.py`) — pure deterministic orchestration,
  **no IO / LLM / clock / randomness in workflow code** — advancing:
  `match & screen → outreach draft → [human approval] → await NDA (durable timer)
  → close`, with **decline** and **NDA-timeout** paths → clean **archive**.
- **Idempotent activities** (mocked under `LLM_MOCK`), keyed by `deal_id`+step:
  `screen_and_match` (canned ranked matches), `draft_outreach` (mock text),
  `persist_*` / `archive_deal` DB writes — safe to retry, never double-send.
- **Human-approval signals:** `approve_outreach` / `decline_outreach`, awaited via
  `workflow.wait_condition`; **durable timer** for the NDA wait.
- The worker registers the workflow + activities (extends the Milestone 0 worker).
- **Minimal API to drive it:** `POST /deals`, `POST /deals/{id}/approve`,
  `POST /deals/{id}/decline`, `GET /deals/{id}`.
- **`make demo`** runs two scenarios and asserts the outcome: (a) start a deal,
  kill + restart the worker mid-flight, approve → workflow completes **exactly
  once**; (b) force a decline / NDA timeout → deal **archived cleanly**.
- **`make test`** includes a `WorkflowReplayer` determinism test that runs with the
  time-skipping test environment — **no live Temporal server required in CI**.

## Smoke check (how you know it worked)
- `make up`, then `make demo`: prints **PASS** for the kill-a-worker resume and
  **PASS** for the decline/timeout archival.
- Temporal UI (`http://localhost:8001`) shows the workflow history surviving the
  worker restart and completing once.
- `make test` is green, including the replay test.

## Explicitly out of scope (later milestones)
- Real embeddings / LLM matching + rationales — Milestone 3 (activities stay stubbed).
- precision@k / recall@k eval — Milestone 4.
- Real agent reasoning (screening / outreach / due-diligence agents) — Milestone 5.
- UI beyond the minimal drive-the-demo endpoints — Milestone 6.

## Stack gotchas
- **Determinism boundary is the whole game:** no `time.time()`, no `asyncio.sleep`,
  no `random`, no network in workflow code — use `workflow.now()` and workflow
  timers; push everything non-deterministic into activities (ADR 0004).
- Activities execute **at-least-once** → must be **idempotent** (`deal_id`+step as
  the key); never double-send outreach.
- The kill demo relies on the **worker being its own container** (it is) so
  `docker compose kill worker` doesn't take down the API or Temporal.
- Use Temporal's **time-skipping test env / `WorkflowReplayer`** for fast,
  deterministic tests; don't depend on a live server in `make test`.
- Keep the pinned images (`temporalio/auto-setup:1.25.2`, `temporalio/ui:2.31.2`,
  `pgvector:pg16`) and the pinned `temporalio` SDK; don't bump versions.

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
> Implement Milestone 2 per this contract. Add a deterministic `DealWorkflow`
> (match → outreach → approval signal → NDA durable timer → close, with
> decline/timeout → archive), idempotent mocked activities, the approval/decline
> signals, worker registration, and the minimal `/deals` API. Wire `make demo` to
> the kill-a-worker resume and the decline/timeout archival, and add a
> `WorkflowReplayer` determinism test to `make test`. Keep all LLM/non-deterministic
> calls in activities and first boot key-free. Validate with `docker compose config
> -q` and `make test`. Commit to `claude/product-thinking-repos-cmbegm` and push.
