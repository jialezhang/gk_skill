---
plan_status: PLAN_REVIEW_REQUIRED
plan_version: 0.1.0
prd_version: ""
approved_by: null
approved_at: null
current_milestone: M1
---

# Implementation Plan: [FEATURE]

## Approved Product Contract

- PRD path/version:
- Blocking journeys:
- Invariants and non-goals:

## Scope Assessment and Goal Packaging

- Scope assessment path/revision:
- P50/P80/P90 wall-clock estimate:
- Split recommendation/decision/source:
- Program baseline: single_goal | multi_goal

| Goal | Independent outcome | P50/P80 | Dependencies | Write conflicts | Session | Worktree/branch | Port/browser context | Checkpoint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Program Dependency and Conflict Graph

```text
[Goal dependency and write-conflict graph]
```

## Model and Agent Budget

- Sol allowed reasons:
- Terra execution stages:
- Luna deterministic verification stages:
- Terra browser/journey/final acceptance stages:
- Sol fallback: current model, live failure evidence, and `sol_route_fallback` record:
- Browser acceptance runner: Ego Lite `ego-browser` exclusively
- Agent target/soft/hard limit: 8 / 12 / 20
- Maximum parallel Goal sessions: 3
- Model-routing Canary evidence:

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
| External effects |  |

## Current-State Evidence

| Evidence | Location/result | Implication |
| --- | --- | --- |

## Change Classification

| Requirement/problem | local fix / compatible extension / incompatible constraint | Evidence | Response |
| --- | --- | --- | --- |

## Commitment Ledger

| ID | Decision | MUST / BASELINE / VERIFY_FIRST / RECOMMENDED / DEFERRED / FORBIDDEN | Evidence | Revision trigger |
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

## 阶段真实用户旅程

- Stage and journey:
- Exact target:
- Ego Lite task-space/URL:
- `ego-browser` actions, observations, evidence paths, and `completeTaskSpace` cleanup:
- Must prove:
- Must not build before gate:
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

## Checkpoint and Integration Plan

| Checkpoint | Goal | Runnable outcome | Required checks | Commit/push/report | Integration order |
| --- | --- | --- | --- | --- | --- |

- Integration owner:
- Integration worktree/branch:
- Clean-commit verification commands:

## Verification Strategy

- `test:fast`:
- `test:change`:
- `test:full` trigger and candidate rule:
- Acceptance claims versus execution scenarios:
- External-effect policies, authorization, and limits:
- Evidence reuse/invalidation keys:
- Cartesian matrix policy:

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

- [ ] The PRD is approved and version-pinned.
- [ ] Every P0/P1 requirement maps to work and evidence.
- [ ] Every blocking journey has an exact-target case.
- [ ] Dependencies, gates, rollback, and escalation are explicit.
- [ ] Provisional detail is not presented as verified fact.
