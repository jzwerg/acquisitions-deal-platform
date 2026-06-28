# ADR 0001 — Temporal for the deal lifecycle

- **Status:** Accepted
- **Context:** An M&A deal is a multi-stage process (match → outreach → NDA → due diligence → negotiation → close) that runs for weeks, pauses on human action, and has steps that can fail, time out, or need rolling back. We must choose how to orchestrate it.

## Decision

Model each deal as a **Temporal workflow**. Each stage is an activity with retries and timeouts; long waits (e.g. awaiting an NDA signature) use **durable timers**; human decisions arrive as **signals**; decline/timeout paths archive the deal cleanly. Temporal owns workflow/process state; PostgreSQL owns deal and profile data.

## Rationale

- **Durable execution.** If a worker crashes mid-deal, Temporal resumes the workflow from its event history exactly where it left off — no manual recovery, no deals stuck in a half-finished state. This is the property that makes long-running, real-world processes reliable, and it is the basis of the headline failure demo.
- **Timers and human-in-the-loop are first-class.** "Wait up to 14 days for an NDA, then escalate or archive" is a one-line durable timer in Temporal. Implemented with cron + a state table it is fragile and verbose.
- **Right fit for agentic systems.** Durable execution is becoming the standard backbone for agent workflows precisely because agent steps are long-running, failure-prone tool calls that need retries and resumability — which is exactly this deal pipeline.

## Alternatives considered

- **Hand-rolled state machine in Postgres + a worker loop.** Reimplements retries, timers, crash recovery, and idempotent step replay — a worse version of what Temporal provides out of the box.
- **A message queue + consumers.** Good for fan-out, but offers no durable workflow state, no built-in human-wait/timer semantics, and no point-in-time resume.

## Consequences

- Activities must be **idempotent** (see ADR 0003): Temporal guarantees at-least-once execution, so retried activities must not double-apply effects.
- A clean boundary is required — Temporal is not the source of truth for business data, and Postgres does not track workflow progress.
- Added operational components (Temporal server + workers) in Docker Compose; in exchange, a workflow-replay test becomes a strong correctness signal in CI.
