# Milestone 1 — Domain & data

The single goal of this milestone: **define the domain (buyer mandates, seller
listings) and a seeded synthetic generator that both the matching layer and the
deal workflow build on.** Still mock-first — `make seed` runs with no API key and
is deterministic (same seed → identical data). This is *not* matching or the
workflow (those come next); it is the data foundation underneath them.

> Milestone 0 (first `docker compose up`) is **done** — see
> [`docs/milestones/milestone-0-first-boot.md`](./docs/milestones/milestone-0-first-boot.md).
> The next milestone is the durable workflow + kill-a-worker demo — see
> [`docs/milestones/milestone-2-durable-workflow.md`](./docs/milestones/milestone-2-durable-workflow.md).

## Definition of done
- **Pydantic v2 models** for `BuyerMandate` and `SellerListing` — structured
  attributes (sector, geography, revenue, EBITDA band, deal-size range) plus the
  free text (strategy / "what good looks like" / business description) the
  matching layer will reason over, with validation.
- **Postgres schema** for mandates + listings, created automatically on `make up`
  (an `init.sql` mounted into the `db` service). Includes
  `CREATE EXTENSION IF NOT EXISTS vector` and a **reserved `embedding vector(N)`
  column that stays NULL** until Milestone 3.
- **Seeded synthetic generator** producing realistic, **regionally-varied**
  profiles (UK / EU / US / SG deal sizes, sectors, EBITDA bands). A pure
  `generate(seed, …)` function (no DB) plus a thin DB-writer. `make seed`
  populates the database; rerunning with the same seed is idempotent (upsert by
  id, no duplicates).
- `make up` still boots healthy with **no API key**; `make test` stays green
  (model validation + generator-determinism tests, no DB required in CI).

## Smoke check (how you know it worked)
- `make up && make seed`, then
  `docker compose exec db psql -U app -d deals -c "select count(*) from listings;"`
  returns a **non-zero** count (same for `mandates`).
- Running `make seed` twice with the same seed leaves the **same row count** (idempotent upsert).
- `make test` passes, including a test asserting the generator is deterministic.

## Explicitly out of scope (later milestones)
- Populating the `embedding` column / any vector similarity — Milestone 3.
- LLM re-ranking and per-match rationales — Milestone 3.
- The Temporal deal-lifecycle workflow + kill-a-worker demo — Milestone 2.
- precision@k / recall@k eval — Milestone 4.

## Stack gotchas
- The `pgvector/pgvector:pg16` image ships the extension but does **not** enable
  it — the `init.sql` must `CREATE EXTENSION IF NOT EXISTS vector`.
- **Pick the embedding dimension now** and reserve the column even though it stays
  NULL until M3 (`EMBEDDING_DIM`, default 1024). The real model choice is an M3 /
  ADR 0002 decision and may change the dimension — keep it a single constant.
- The generator must be **deterministic** — seed the RNG, no wall-clock, no
  unseeded randomness — so the M4 eval and the tests are reproducible.
- **Keep CI DB-free:** the pure `generate(...)` function and model validation are
  unit-tested; the DB write path is exercised by `make seed`, not by `pytest`.
- **DB access:** SQLAlchemy 2.0 (async, `asyncpg` driver) for legibility — pick
  one access layer and keep it consistent across the project.
- Determinism boundary still holds: **no LLM calls anywhere in M1** (data
  generation is pure); LLM work lives in activities from M3 on (ADR 0004).

## Shared conventions (portfolio-wide — keep identical across all four repos)
- **Branch:** `claude/product-thinking-repos-cmbegm`.
- **Task interface:** `make up` / `down` / `demo` / `test` / `logs` (plus `seed`).
- **First boot needs no secrets** — `.env.example` defaults must boot (LLM mocked).
- **Compose v2:** `docker compose` (space), not the deprecated `docker-compose`.
- **Host ports:** this project owns the **80xx** range.
- **Validate without a daemon:** `docker compose config -q` parses the stack even
  where Docker can't run (e.g. a Claude Code web session); a real boot must be
  verified on a machine with a Docker daemon.

## Paste-ready session kickoff
> Implement Milestone 1 per `MILESTONE.md`. Add Pydantic v2 models for
> `BuyerMandate` and `SellerListing`, a Postgres `init.sql` (with the pgvector
> extension and a reserved NULL `embedding vector(N)` column) applied on `make
> up`, and a seeded, regionally-varied synthetic generator wired to `make seed`
> (deterministic, idempotent upsert). Keep first boot key-free and CI DB-free —
> unit-test the pure generator + model validation. Don't build matching, the
> workflow, or the eval yet. Validate with `docker compose config -q` and `make
> test`. Commit to `claude/product-thinking-repos-cmbegm` and push.
