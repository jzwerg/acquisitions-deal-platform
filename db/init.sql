-- Schema for buyer mandates and seller listings (Milestone 1).
-- Applied automatically by the pgvector/postgres image on first boot
-- (mounted into /docker-entrypoint-initdb.d/). Runs only when the data volume
-- is empty; `make down` removes the volume so the next `make up` re-applies it.
--
-- The `embedding vector(1024)` columns are RESERVED for Milestone 3 and stay
-- NULL until then. The dimension must match app.config.EMBEDDING_DIM.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS mandates (
    id                 TEXT PRIMARY KEY,
    buyer_name         TEXT NOT NULL,
    sectors            TEXT[] NOT NULL,
    regions            TEXT[] NOT NULL,
    revenue_min        DOUBLE PRECISION,
    revenue_max        DOUBLE PRECISION,
    target_ebitda_band TEXT NOT NULL,
    deal_size_min      DOUBLE PRECISION NOT NULL,
    deal_size_max      DOUBLE PRECISION NOT NULL,
    criteria           TEXT NOT NULL,
    embedding          vector(1024),   -- reserved for Milestone 3; NULL until then
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS listings (
    id            TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    sector        TEXT NOT NULL,
    region        TEXT NOT NULL,
    revenue       DOUBLE PRECISION NOT NULL,
    ebitda        DOUBLE PRECISION NOT NULL,
    ebitda_band   TEXT NOT NULL,
    asking_min    DOUBLE PRECISION NOT NULL,
    asking_max    DOUBLE PRECISION NOT NULL,
    description   TEXT NOT NULL,
    embedding     vector(1024),   -- reserved for Milestone 3; NULL until then
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Deal state (Milestone 2). Temporal owns the workflow/process; this table is
-- the business record. Written idempotently by the deal activities (upsert by
-- deal_id), so at-least-once execution never corrupts state.
CREATE TABLE IF NOT EXISTS deals (
    deal_id        TEXT PRIMARY KEY,
    mandate_id     TEXT,
    stage          TEXT NOT NULL,
    outcome        TEXT,           -- closed | archived (set at terminal state)
    reason         TEXT,           -- completed | declined | nda_timeout
    top_match_id   TEXT,
    outreach_draft TEXT,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
