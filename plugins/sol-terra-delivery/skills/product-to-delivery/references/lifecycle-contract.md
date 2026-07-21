# Lifecycle Contract

## State machine

```text
DISCOVERY_IN_PROGRESS
→ DISCOVERY_READY
→ PRD_DRAFT
→ REVIEW_REQUIRED
→ APPROVED
→ SCOPE_ASSESSMENT
→ GOAL_BOUNDARIES_DECIDED
→ PLAN_DRAFT
→ PLAN_REVIEW_REQUIRED
→ PLAN_APPROVED
→ DELIVERY_ACTIVE
→ GATE_REVIEW
→ TARGET_VERIFIED
→ COMPLETE
```

Exceptional states:

- `DISCOVERY_BLOCKED`: a material product choice is missing.
- `READINESS_BLOCKED`: implementation direction lacks decisive repository or runtime evidence.
- `PLAN_CONFLICT`: execution evidence contradicts the approved baseline.
- `PRODUCT_DECISION_REQUIRED`: resolving a conflict changes the approved PRD.
- `VERIFICATION_BLOCKED`: the exact target cannot be exercised.

## Required artifacts

Use the active Spec Kit feature directory when present. Otherwise use the repository's established docs convention.

| Stage | Durable artifact |
| --- | --- |
| Discovery | completed conversation and optional `discovery.md` |
| Product | `spec.md` with approval metadata |
| Scope | `scope-assessment.yaml` with P50/P80/P90 and split decision |
| Planning | program/Goal `plan.md`, `tasks.md`, `verification.md` |
| Delivery | per-Goal `delivery-state.yaml`, `model-routing.jsonl`, decision log, evidence files |
| Integration | integration commit, merge/evidence index, program status |

## Handoffs

- Discovery → PRD: confirmed product decisions, unresolved product questions, acceptance intent, non-goals.
- PRD → scope: only an `APPROVED` product contract.
- Scope → plan: validated estimate, Goal packaging decision, dependency/conflict graph, and decision source.
- Plan → delivery: only `PLAN_APPROVED` artifacts with task IDs, dependencies, Goal/worktree/session ownership, gates, checkpoints, and completion criteria.
- Delivery → review: current revision IDs, clean commit, diff, test output, runtime evidence, model-routing records, deviations, and escalation packet.

## Change ownership

Change only the plan for module layout, SDK behavior, task order, test mechanics, or another technical path that preserves the PRD.

Reopen the PRD for changed user flows, P0/P1 scope, product invariants, safety rules, data ownership, acceptance outcomes, release scope, or significant cost.

## Small-task bypass

For a local, reversible change with clear acceptance and no cross-boundary risk, bypass the full product lifecycle. Do not manufacture a PRD to justify ordinary maintenance.
