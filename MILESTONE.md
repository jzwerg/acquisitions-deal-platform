# Milestone 4 — Matching eval (precision@k / recall@k)

The single goal of this milestone: **make matching quality measurable, not a
vibe.** A labeled synthetic dataset + a precision@k / recall@k harness that
reports a real score for the Milestone 3 retrieval + re-rank pipeline. Runs
deterministically on the **mock** embedding backend so CI reports a stable
number with no API key.

> Done so far: M0 (first boot), M1 (domain & data), M2 (durable workflow +
> kill-a-worker demo), M3 (matching layer) — see
> [`docs/milestones/`](./docs/milestones/). The next milestone is real,
> human-gated agent activities — see
> [`docs/milestones/milestone-5-agentic-activities.md`](./docs/milestones/milestone-5-agentic-activities.md).

## Definition of done
- **Labeled synthetic set**: extend the seeded generator to emit ground-truth
  relevant listing(s) per mandate — plant known-good matches (aligned sector /
  region / band / size) alongside controlled distractors, **deterministic by
  seed** and reproducible from the same RNG as the profiles.
- **Eval harness**: compute **precision@k** and **recall@k** over the M3
  retrieval + re-rank pipeline against those labels, for configurable `k`.
- **`make eval`** prints the scores (a per-`k` table + an aggregate line) and
  states which backend produced them (mock vs real).
- A test asserts the harness runs and that scores on the **mock** backend are
  deterministic and within sane bounds — so CI carries a real, stable number.
- Wire the eval into CI as the "matching quality is measured" proof.

## Smoke check (how you know it worked)
- `make up && make seed && make embed && make eval` prints precision@k / recall@k.
- Re-running `make eval` with the same `SEED` yields the **same** scores.
- `make test` passes, including the eval determinism test.

## Explicitly out of scope (later milestones)
- Real-model tuning / choosing a production embedding+LLM backend — that's the
  opt-in real path established in M3/M5, not this eval.
- Real agent reasoning (M5), UI (M6), failure-demo polish / CI-runs-the-demo (M7–8).

## Stack gotchas
- The labeled set **must be deterministic** (seeded) or the eval isn't
  reproducible — derive relevance labels from the same seed as the profiles so
  planted matches are stable.
- Report the CI number on the **mock** backend (no key); a real-backend run is
  local and opt-in. Always state which backend a reported score came from.
- Keep the eval logic **DB-optional** where practical (evaluate over an in-memory
  candidate set built from the generator) so `make test` stays DB-free; gate any
  pgvector-backed retrieval test to the live stack.
- The eval measures the pipeline behind the activity boundary — no LLM/embedding
  calls leak into workflow code (ADR 0004).

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
> Implement Milestone 4 per `MILESTONE.md`. Extend the seeded generator with
> ground-truth relevance labels, add a precision@k / recall@k harness over the M3
> matching pipeline wired to `make eval`, and a determinism test that reports a
> stable score on the mock backend in CI. Keep it key-free, reproducible, and
> DB-free where practical. Don't build real agent activities or a UI yet.
> Validate with `docker compose config -q` and `make test`. Commit to
> `claude/product-thinking-repos-cmbegm` and push.
