# Milestone 3 — Matching layer (embeddings + LLM re-rank)

The single goal of this milestone: **turn mandates and listings into ranked,
explained matches.** Embed profiles into pgvector, retrieve candidates by vector
similarity + structured filters, then **LLM re-rank** the shortlist against the
mandate's criteria — each match carrying a **written rationale**. This plugs into
the existing `screen_and_match` activity, so the deal workflow is unchanged.
Still mock-first: deterministic mock embeddings + mock re-rank mean `make up` and
CI run with **no API key**; real embeddings/LLM turn on behind `LLM_MOCK=false`.

> Done so far: M0 (first boot), M1 (domain & data), M2 (durable workflow +
> kill-a-worker demo) — see [`docs/milestones/`](./docs/milestones/). The next
> milestone is the matching eval — see
> [`docs/milestones/milestone-4-matching-eval.md`](./docs/milestones/milestone-4-matching-eval.md).

## Definition of done
- **Embedding provider abstraction** with two backends selected by `LLM_MOCK`:
  a **deterministic mock** (hash-seeded vector of `EMBEDDING_DIM`, no network,
  the default) and a **real** backend (a configured embeddings API, only when
  `LLM_MOCK=false`). Anthropic has no embeddings API, so the real backend is a
  separate provider behind this abstraction — out of the first-boot path.
- **Embedding population**: a step (`make embed`) that computes embeddings for
  seeded mandates + listings and writes them to the reserved `embedding` column.
- **Candidate retrieval**: structured pre-filter (sector / region / EBITDA band /
  deal-size) **plus** pgvector similarity (cosine `<=>`) over listings for a
  mandate → a top-N shortlist.
- **LLM re-rank**: score the shortlist against the mandate criteria and attach a
  **per-match rationale**; mocked deterministically under `LLM_MOCK`.
- **Wired into the workflow**: `screen_and_match` returns these real ranked
  matches (with rationale) instead of canned ones — same activity boundary, the
  workflow untouched.
- `make up` still boots healthy with **no API key**; `make test` stays green
  (retrieval + mock-embedding + re-rank tests; keep DB-touching tests gated so CI
  logic stays DB-free).

## Smoke check (how you know it worked)
- `make up && make seed && make embed`, then
  `docker compose exec db psql -U app -d deals -c "select count(*) from listings where embedding is not null;"`
  returns a **non-zero** count.
- Start a deal (`POST /deals`) → the returned match(es) carry a **rationale** and
  the `deals` record's `top_match_id` comes from real retrieval, not a constant.
- `make test` passes, including a deterministic re-rank/retrieval test.

## Explicitly out of scope (later milestones)
- precision@k / recall@k eval + the labeled set — Milestone 4.
- Real agent reasoning for screening/outreach/DD — Milestone 5.
- UI beyond the existing endpoints — Milestone 6.
- The failure-demo polish / CI-runs-the-demo — Milestone 7–8.

## Stack gotchas
- Keep `EMBEDDING_DIM` in sync with the `vector(N)` column in `db/init.sql`. If
  the real model's dimension differs, that's a **schema change** — document it.
- **Mock embeddings must be deterministic** (hash/seed-based) so retrieval, the
  re-rank, and the M4 eval are all reproducible.
- Determinism boundary (ADR 0004): embeddings + LLM re-rank calls run **inside
  the `screen_and_match` activity**, never in workflow code — the boundary is
  already in place, keep it.
- pgvector similarity uses the `<=>` operator; an ivfflat/hnsw index is optional
  at demo scale but note it for larger corpora.
- **No new services**; embeddings are computed in-process / in the activity.

## Shared conventions (portfolio-wide — keep identical across all four repos)
- **Branch:** `claude/product-thinking-repos-cmbegm`.
- **Task interface:** `make up` / `down` / `demo` / `test` / `logs` (plus `seed`, `embed`).
- **First boot needs no secrets** — `.env.example` defaults must boot (LLM mocked).
- **Compose v2:** `docker compose` (space), not the deprecated `docker-compose`.
- **Host ports:** this project owns the **80xx** range.
- **Validate without a daemon:** `docker compose config -q` parses the stack even
  where Docker can't run (e.g. a Claude Code web session); a real boot must be
  verified on a machine with a Docker daemon.

## Paste-ready session kickoff
> Implement Milestone 3 per `MILESTONE.md`. Add an embedding provider abstraction
> (deterministic mock default, real behind `LLM_MOCK=false`), a `make embed` step
> that populates the pgvector `embedding` columns, candidate retrieval (structured
> filter + cosine similarity), and an LLM re-rank producing a per-match rationale
> — then have the `screen_and_match` activity return those real matches without
> changing the workflow. Keep first boot key-free and the re-rank/embeddings
> mocked deterministically. Don't build the precision@k eval yet. Validate with
> `docker compose config -q` and `make test`. Commit to
> `claude/product-thinking-repos-cmbegm` and push.
