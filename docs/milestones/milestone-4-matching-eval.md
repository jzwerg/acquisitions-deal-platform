# Milestone 4 — Matching eval (precision@k / recall@k)

The single goal of this milestone: **make matching quality measurable, not a
vibe.** A labeled synthetic dataset + a precision@k / recall@k harness that
reports a real score for the Milestone 3 retrieval + re-rank pipeline. Runs
deterministically on mock embeddings so CI reports a stable number with no API
key.

> Prerequisite: Milestone 3 (matching layer). The eval measures that pipeline.

## Definition of done
- **Labeled synthetic set**: extend the seeded generator to emit ground-truth
  relevant listing(s) per mandate (plant known-good matches with controlled
  distractors), deterministic by seed.
- **Eval harness**: compute **precision@k** and **recall@k** over the
  retrieval + re-rank pipeline against the labels, for configurable `k`.
- **`make eval`** prints the scores (per-k table + aggregate).
- A test asserts the harness runs and that scores on **mock embeddings** are
  deterministic and within sane bounds (so CI has a real, stable number).
- Wire the eval into CI as the "matching quality is measured" proof.

## Smoke check (how you know it worked)
- `make up && make seed && make embed && make eval` prints precision@k / recall@k.
- Re-running `make eval` with the same seed yields the **same** scores.
- `make test` passes, including the eval determinism test.

## Explicitly out of scope (later milestones)
- Real-model tuning / provider selection beyond what M3 established.
- Real agent reasoning (M5), UI (M6), failure-demo polish (M7–8).

## Stack gotchas
- The labeled set must be **deterministic** (seeded) or the eval isn't
  reproducible — plant relevance labels from the same RNG as the profiles.
- Report the score on the **mock** backend in CI (no key); the real backend is a
  local, opt-in run. State which backend produced a reported number.
- Keep the eval logic **DB-optional** where possible (evaluate over in-memory
  candidates) so CI doesn't require Postgres; gate any DB-backed retrieval test.

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
> Implement Milestone 4 per this contract. Extend the seeded generator with
> ground-truth relevance labels, add a precision@k / recall@k harness over the
> M3 pipeline wired to `make eval`, and a determinism test that reports a stable
> score on mock embeddings in CI. Keep it key-free and reproducible. Validate
> with `docker compose config -q` and `make test`. Commit to
> `claude/product-thinking-repos-cmbegm` and push.
