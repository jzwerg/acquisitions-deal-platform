# ADR 0002 — Hybrid matching: embeddings + LLM re-rank

- **Status:** Accepted
- **Context:** The platform must match buyer acquisition mandates to seller listings. Mandates and listings mix structured attributes (sector, geography, revenue, EBITDA band) with free text (strategy, rationale, "what good looks like"). We must choose a matching approach that is both effective and explainable.

## Decision

Use a **hybrid pipeline**: (1) structured pre-filtering + **vector similarity** over embeddings (pgvector) for candidate retrieval, then (2) **LLM re-ranking** of the top candidates against the mandate's explicit criteria, producing a score **and a written rationale** per match.

## Rationale

- **Retrieval vs. judgment are different jobs.** Embeddings are fast and cheap for narrowing thousands of listings to a shortlist; an LLM is expensive but good at nuanced judgment over a handful of candidates. Doing each where it is strong keeps cost bounded and quality high.
- **Explainability.** A bare similarity score is unconvincing to a user deciding whether to pursue a deal. The LLM re-rank attaches a rationale ("matches sector and size; mismatched geography but stated openness to relocation"), which is both better UX and a stronger portfolio signal.
- **Evaluable.** The pipeline is measured with precision@k / recall@k over a labeled synthetic dataset, so quality is reported, not asserted.

## Alternatives considered

- **Pure vector similarity.** Fast and simple, but no reasoning over criteria and no rationale; struggles with hard constraints (e.g. "must be profitable").
- **Pure LLM over the full corpus.** Highest judgment quality but does not scale — re-ranking every listing per query is cost-prohibitive and slow.

## Consequences

- A two-stage pipeline adds complexity and a tuning surface (how many candidates to re-rank, embedding model choice).
- Re-rank cost scales with shortlist size, not corpus size — a deliberate, bounded tradeoff.
- The eval harness and labeled synthetic set become first-class deliverables that demonstrate the quality of the matching, not just its existence.
