---
plan_status: PLAN_REVIEW_REQUIRED
plan_version: 0.1.0
prd_version: ""
approved_by: null
approved_at: null
target_repository: ""
current_milestone: M1
---

# Implementation Plan: [Feature]

## Product Outcome and Approved Scope

- PRD:
- Blocking journeys:
- Non-goals:

## Requirement Traceability

| Requirement | Journey | Milestone | Tasks | Automated evidence | Exact-target case | Gate |
| --- | --- | --- | --- | --- | --- | --- |

## Target Identity

| Surface | Exact target |
| --- | --- |
| Product/module |  |
| Entry point |  |
| API/routes |  |
| Services/repositories |  |
| Stores |  |
| Flags/build |  |
| User/owner |  |
| Providers |  |

## Current-State Evidence

| Evidence | Location/result | Implication |
| --- | --- | --- |

## Change Classification

| Requirement/problem | Classification | Evidence | Planned response |
| --- | --- | --- | --- |

## Commitment Ledger

| ID | Decision | Level | Evidence | Revision trigger |
| --- | --- | --- | --- | --- |

## Assumption Ledger

| ID | Assumption | Confidence | Verify in | Consequence if false |
| --- | --- | --- | --- | --- |

## Responsibility Replacement

| Responsibility | Current owner | New owner | Handoff condition | Legacy disposition |
| --- | --- | --- | --- | --- |

## Data, Identity, and Safety Flow

| Field/fact | Source | Validation | Persistence | Consumer | Recovery |
| --- | --- | --- | --- | --- | --- |

## Runtime Lifecycle and State Convergence

- Applicability: applicable | not applicable, with evidence
- Authoritative business-state owner:
- Terminal states:
- Convergence objective:

| Lifecycle | Identity/correlation key | Owner | Nonterminal states | Terminal states | Observation/recovery |
| --- | --- | --- | --- | --- | --- |

| Consumer surface | Initial snapshot | Live update | Gap/reconnect reconciliation | Ordering/idempotency | Stale-action protection |
| --- | --- | --- | --- | --- | --- |

- Invariants, including why interaction or transport completion cannot prematurely terminate business-work observation:
- Fault cases that must be proven on the exact target:

## First Realistic Vertical Slice

- Journey:
- Exact target:
- Must prove:
- Explicitly excluded before the gate:
- Falsifiers and stop actions:

## Complete Milestone Baseline

| Milestone | Outcome | Major tasks | Entry gate | Exit gate |
| --- | --- | --- | --- | --- |

## Dependency Graph

```text
[task and gate DAG]
```

## Delegation Map

| Task | Preferred role | Required skills | Write scope | Parallel with | Reviewer |
| --- | --- | --- | --- | --- | --- |

## Verification Strategy

- Focused checks:
- Integration checks:
- Exact-target cases:
- Regression:
- Lifecycle interruption and convergence checks when applicable:

## Plan Review Record

- Reviewer:
- Reviewed revisions:
- Blocking findings resolved:
- Major findings resolved:
- Remaining non-blocking findings:
- Verdict:

## Rollout, Rollback, and Legacy

- Enable path:
- Rollback trigger and operation:
- Protected data:
- Legacy downgrade/delete conditions:

## Plan Revision Protocol

- Local deviation:
- Plan-level contradiction:
- Product-level conflict:
- Attempt invalidation rule:

## Remaining Risks

| Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |

## Approval Checklist

- [ ] PRD is approved and version-pinned.
- [ ] Every P0/P1 requirement maps to tasks and evidence.
- [ ] Every blocking journey has an exact-target case.
- [ ] Dependencies, gates, rollback, and escalation are explicit.
- [ ] Provisional details are not presented as verified facts.
- [ ] Long-running journeys define authoritative state, subscription lifetime, reconciliation, convergence, and stale-action protection.
