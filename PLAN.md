# Build Plan — Acquisitions Deal Platform

## Goal

An AI-matched M&A marketplace where each deal runs as a durable Temporal workflow: buyers post mandates, sellers list businesses, an AI layer produces ranked and explained matches, and the deal lifecycle (match → outreach → NDA → due diligence → negotiation → close) is orchestrated to survive crashes, retries, and long human-in-the-loop waits.

## Definition of done

`docker-compose up` brings up Temporal, workers, Postgres (+pgvector), and the API. A buyer mandate and a set of seller listings produce ranked matches with written rationales; starting a deal launches a Temporal workflow that advances through approval gates. Two demos pass:

1. **Durable orchestration:** kill a Temporal worker mid-deal — the workflow resumes and completes exactly once; a declined outreach or NDA timeout archives the deal cleanly with no orphaned state.
2. **Matching quality:** a precision@k eval over a labeled synthetic dataset reports a measured score, not a vibe.

## Milestones

1. **Domain & data** — schemas for buyer mandates and seller listings; a synthetic generator producing realistic, regionally-varied profiles (UK/EU/US/SG deal sizes, sectors, EBITDA bands).
2. **Matching layer** — embed mandates and listings into pgvector; candidate retrieval by vector similarity + structured filters; **LLM re-ranking** against explicit criteria with a per-match rationale.
3. **Matching eval** — a labeled synthetic set + precision@k / recall@k harness.
4. **Temporal deal-lifecycle workflow** — activities for match & screen → outreach draft → await NDA (durable timer) → due-diligence checklist agent → negotiation tracking → close; human-approval signals and decline/timeout archival paths.
5. **Agentic activities** — screening, outreach drafting, and due-diligence agents as idempotent Temporal activities; agents propose, humans approve before external actions.
6. **API + minimal UI** — endpoints (and a thin UI) to post mandates/listings, view ranked matches, and drive approval gates.
7. **Failure demos** — (a) kill a worker mid-workflow; (b) force a decline/timeout and show clean archival.
8. **Polish** — README diagram, ADRs, GitHub Actions CI with a meaningful test suite (including a workflow-replay test).

## Key technical challenges

- **Idempotent activities** — Temporal executes activities at-least-once, so any agent or DB activity must be safe to retry (use the deal/step id as an idempotency key; never double-send outreach).
- **Bounded agent autonomy** — agents draft and propose; nothing external (email, NDA request) is sent without a human-approval signal. This boundary is a deliberate trust/safety design point.
- **Matching that is explainable and evaluable** — avoid an opaque score; every match carries a rationale, and quality is measured rather than asserted.
- **Clean separation** — Temporal owns workflow/process state; Postgres owns deal and profile data. The workflow must not become the source of truth for business data.

## Decisions captured

- **Temporal for the deal lifecycle** — `docs/adr/0001-temporal-deal-lifecycle.md`.
- **Hybrid matching (embeddings + LLM re-rank)** — `docs/adr/0002-matching-architecture.md`.
- **Agent activity design (idempotent, human-gated)** — `docs/adr/0003-agent-activity-design.md`.
