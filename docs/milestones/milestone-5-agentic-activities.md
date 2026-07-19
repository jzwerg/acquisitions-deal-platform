# Milestone 5 — Agentic activities (real LLM, human-gated)

The single goal of this milestone: **turn the mocked agent steps into real,
idempotent, human-gated Temporal activities.** Screening, outreach drafting, and
a due-diligence checklist agent that call the Claude API — behind
`LLM_MOCK=false` — while first boot and CI stay mock-first and key-free. Agents
**propose**; humans **approve** before anything external happens (the approval
gate already exists from M2).

> Prerequisite: M2 (workflow + approval signal) and M3 (matching pipeline). This
> fills in the real backends that M3 stubbed behind `LLM_MOCK=false`.

## Definition of done
- **Real LLM re-rank** (fills `app.matching._real_rerank`): score the shortlist
  against the mandate criteria and produce a written rationale via Claude, behind
  `LLM_MOCK=false` with `ANTHROPIC_API_KEY` set. Latest Claude models (see the
  `claude-api` skill); a cheap model for the cheap step, a stronger one for
  reasoning-heavy steps.
- **Real outreach drafting** (fills `draft_outreach`'s real path): a drafted note
  the human approves before send.
- **Due-diligence checklist agent** as an activity that proposes a checklist for
  an approved deal.
- **Idempotent + bounded autonomy**: every agent activity is safe to retry
  (deal/step id as idempotency key) and never triggers an external side effect
  without the human-approval signal (ADR 0003).
- **Mock-first preserved**: `LLM_MOCK=true` still boots and passes CI with no
  key; the real path is exercised only when a key is present.
- Determinism boundary (ADR 0004): all LLM calls stay inside activities.

## Smoke check (how you know it worked)
- With `LLM_MOCK=true` (default): `make up` + `make demo` + `make test` all pass,
  no key required (unchanged).
- With `LLM_MOCK=false` + `ANTHROPIC_API_KEY`: starting a deal produces an
  LLM-written rationale and outreach draft; re-running an activity yields no
  duplicate side effects.

## Explicitly out of scope (later milestones)
- API surface expansion + a thin UI — Milestone 6.
- Failure-demo polish / CI-runs-the-headline-demo — Milestone 7.
- README diagram refresh, ADR updates, replay-test-in-CI polish — Milestone 8.

## Stack gotchas
- Keep the **mock/real split behind the existing abstractions** (`app.embeddings`,
  `app.matching`, the activity mocks) — no new branching in workflow code.
- **Idempotency is not optional**: Temporal runs activities at-least-once; guard
  external actions with an idempotency key and the approval signal.
- Never require a key for first boot or CI — the real path is strictly opt-in.
- Load the `claude-api` skill for current model ids, pricing, and tool-use
  patterns before writing Claude calls; don't hardcode stale model names.

## Shared conventions (portfolio-wide — keep identical across all four repos)
- **Branch:** `claude/product-thinking-repos-cmbegm`.
- **Task interface:** `make up` / `down` / `demo` / `test` / `logs` (plus `seed`, `embed`, `eval`).
- **First boot needs no secrets** — `.env.example` defaults must boot (LLM mocked).
- **Compose v2:** `docker compose` (space), not the deprecated `docker-compose`.
- **Host ports:** this project owns the **80xx** range.
- **Validate without a daemon:** `docker compose config -q` parses the stack even
  where Docker can't run (e.g. a Claude Code web session); a real boot must be
  verified on a machine with a Docker daemon.

## Paste-ready session kickoff
> Implement Milestone 5 per this contract. Fill in the real (LLM_MOCK=false)
> backends stubbed in M3 — Claude-based re-rank with rationale and outreach
> drafting — plus a due-diligence checklist agent, all as idempotent, human-gated
> Temporal activities. Keep LLM_MOCK=true booting and CI green with no key; keep
> all LLM calls inside activities. Load the claude-api skill for current model
> ids first. Validate with `docker compose config -q` and `make test`. Commit to
> `claude/product-thinking-repos-cmbegm` and push.
