# ADR 0004 — Agent runtime and model hosting (demo scope vs. end goal)

- **Status:** Accepted (demo scope); end-state documented
- **Context:** The agent steps (screening, outreach drafting, due-diligence checklist) need a runtime for their reasoning logic, and the system needs an LLM. We must decide what to build for this demo versus what the production architecture would be — and record the gap honestly.

## Decision

**For this demo:**
- **Temporal is the sole orchestrator** of the deal lifecycle. Agent reasoning runs inside Temporal activities as small, explicit loops that **call the Claude API directly**.
- We do **not** introduce a second orchestration/graph framework (e.g. LangGraph) in the demo.

**End goal (documented, not built here):**
- **Graph-structured agents** (e.g. LangGraph) for the in-step agent reasoning, where multi-branch agent logic justifies a graph runtime — composed *inside* Temporal activities, with **Temporal remaining the single owner of the durable, long-running deal lifecycle**.
- **Managed or self-hosted models** rather than a direct third-party API: a managed model on the cloud provider of choice, or a self-hosted open-source model, for data-residency, cost, and control reasons appropriate to handling confidential M&A data.

## Rationale

- **One orchestrator, no overlap.** Temporal and graph-agent frameworks both offer orchestration, persistence, and human-in-the-loop. Stacking them in a demo invites a "why two orchestrators?" critique. The clean, defensible story is: Temporal owns the *durable lifecycle*; agent frameworks, if added, own only *in-step reasoning* and run as activities.
- **Determinism boundary.** Temporal workflow code must be deterministic; all LLM calls and any graph-driven (non-deterministic) control flow must live inside activities. This constraint holds in both the demo and the end-state and is what keeps the integration clean.
- **Demo simplification is explicit.** Calling Claude directly keeps the demo small and the architecture legible. The production reality — managed/self-hosted models for confidential data — is recorded here so the simplification is a stated choice, not an oversight.

## Consequences

- Agent activities remain idempotent and human-gated (see ADR 0003), independent of whether the runtime is a direct loop or a graph framework — so adopting graph-structured agents later does not change the workflow contract.
- Swapping the model provider (direct API → managed/self-hosted) is isolated behind the activity boundary: the workflow and orchestration are unaffected.
- The path from demo to end-state is additive (introduce a graph runtime inside existing activities; swap the model backend), not a rewrite.
