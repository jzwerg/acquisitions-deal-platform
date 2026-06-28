# Product Brief — Acquisitions Deal Platform

> Engineering decisions live in [`docs/adr/`](../adr/). This brief is the product
> counterpart: who it's for, what success looks like, and what we deliberately
> don't build.

## The problem
Lower-middle-market M&A (SMB deals, ~£1–50M) runs on email, spreadsheets, and
relationships. Two failures repeat: (1) **sourcing is slow and opaque** — finding
the right buyer for a listing is manual and relationship-bound; (2) **deals die in
the gaps** — a multi-week process with NDA waits, approvals, and handoffs loses
context and momentum, and deals silently stall with no owner and no next step.

## Who it's for
- **Primary user:** the deal lead / associate at a boutique M&A advisory or search
  fund who shepherds deals through stages.
- **Economic buyer:** the advisory principal / fund partner who pays for throughput
  and fewer dropped deals.
- **It is the advisor's tool — not a replacement for the advisor.** (See non-goals.)

## Job to be done
"When a business comes to market, help me find the right buyer and move the deal to
close — without it dying in the weeks-long gaps between steps."

## What success looks like
- **North Star — no deal stalls silently:** % of active deals that always have an
  owner, a next action, and a deadline. Target ≈100%. *(This is the product
  expression of durable execution — the reason Temporal is here.)*
- **Value metrics:** time-to-first-qualified-match · match-acceptance rate (do users
  pursue the AI's matches?) · median deal cycle time · advisor-hours saved per deal.
- **Quality / engineering metrics:** matching precision@k (eval harness) · workflow
  resumes exactly-once after crash · zero double-sent outreach.

## Non-goals (what we deliberately don't build)
- **Not an autonomous deal-closer.** Agents propose; humans approve every external
  action ([ADR 0003](../adr/0003agentactivitydesign.md)). Bounded autonomy is a
  product stance, not a limitation.
- **Not legal execution** — no e-signature, escrow, or funds flow. We integrate.
- **Not a valuation / financial-modeling engine**, and **not a virtual data room.**
- **Not large-cap / investment-bank-grade deals** — focus is SMB / lower-mid-market.
- **Not a CRM replacement.**

## Sequencing — prove the riskiest assumption first
The riskiest *product* bet isn't "can it survive a crash" (we know Temporal can) —
it's **"will a deal lead trust an AI match enough to act on it?"** So the walking
skeleton is matching-first:

1. One mandate + a handful of listings → **ranked, explained matches** + the eval.
   *(De-risks trust before we build any lifecycle.)*
2. Start a deal → it advances through **one** human-approved gate.
3. Kill a worker mid-deal → it **resumes exactly where it left off.**

That single thread proves both halves; everything else thickens around it.

## Key risks & assumptions
- **Two-sided cold-start (biggest risk).** A marketplace needs buyers *and* sellers.
  Demo: synthetic, regionally-varied data. Real: seed sell-side-led through advisor
  relationships before opening buy-side.
- **Trust in AI matches.** Mitigated by a per-match rationale + a published eval
  score + the human gate — match quality is *shown*, not asserted
  ([ADR 0002](../adr/0002matchingarchitecture.md)).
- **Confidentiality.** M&A data is highly sensitive; data residency / leakage is an
  adoption blocker. The demo calls Claude directly; the production path is
  managed / self-hosted models ([ADR 0004](../adr/0004agentruntimeandmodelhosting.md))
  — recorded so the gap is a stated choice, not an oversight.
- **Disintermediation fear.** Advisors resist tools that connect buyers and sellers
  directly. Positioning: it makes the advisor faster, it doesn't cut them out.

## The demo, framed as a user outcome
A £4M deal is 11 days into a 14-day NDA wait when the infrastructure crashes.
Nothing is lost: the workflow resumes, the durable timer still fires on day 14, the
deal lead never even knew there was an outage — and the deal didn't quietly die in
the gap. *That's the promise: no deal stalls because a human or a machine dropped
the ball.*
