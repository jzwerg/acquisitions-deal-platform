# ADR 0003 — Agent activity design: idempotent and human-gated

- **Status:** Accepted
- **Context:** Several deal-lifecycle steps are performed by LLM agents (screening, outreach drafting, due-diligence checklist generation). These run as Temporal activities, which execute at-least-once, and some of them could trigger real-world side effects (sending an email, requesting an NDA). We must define how agents behave within the workflow.

## Decision

1. **Agents propose; humans dispose.** No agent action with an external side effect is executed without an explicit human-approval signal. Agents draft and recommend; a human approves before anything leaves the system.
2. **Activities are idempotent.** Every agent/DB activity is keyed by the deal id + step id so that a Temporal retry re-uses the prior result rather than producing a second effect (e.g. never sends a second outreach message).

## Rationale

- **Trust and safety.** In M&A, an erroneous automated outreach or a leaked detail is a real-world harm. A human-approval gate bounds agent autonomy to drafting, which is where LLMs are genuinely useful and low-risk.
- **Correctness under retry.** Temporal's at-least-once execution means a non-idempotent side-effecting activity could fire twice on transient failure. Idempotency keys make retries safe — a prerequisite, not an optional nicety.
- **Auditability.** Storing each agent proposal and the human decision against the deal gives a clear, reviewable trail of who approved what.

## Alternatives considered

- **Fully autonomous agents.** Faster in the happy path, but unacceptable risk for irreversible external actions and far harder to make safe under retry.
- **No idempotency, rely on "it rarely fails twice."** Incorrect by construction; double-sends are exactly the failure mode users would never forgive.

## Consequences

- The workflow has explicit approval-gate signals, adding states but making behavior predictable and safe.
- Agent activities must persist their proposed output and an idempotency key before any external call; this is enforced at the activity boundary and exercised by the failure-demo tests.
