# Lifecycle Contract

## State machine

```text
DISCOVERY_IN_PROGRESS
→ DISCOVERY_READY
→ PRD_DRAFT
→ REVIEW_REQUIRED
→ APPROVED
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
| Planning | `plan.md`, `tasks.md`, `verification.md` |
| Delivery | `delivery-state.yaml`, `decision-log.md`, evidence files |

## Handoffs

- Discovery → PRD: confirmed product decisions, unresolved product questions, acceptance intent, non-goals.
- PRD → plan: only an `APPROVED` product contract.
- Plan → delivery: only `PLAN_APPROVED` artifacts with task IDs, dependencies, role guidance, gates, and completion criteria.
- Delivery → Sol review: current revision IDs, diff, test output, runtime evidence, deviations, and escalation packet.

## Change ownership

Change only the plan for module layout, SDK behavior, task order, test mechanics, or another technical path that preserves the PRD.

Reopen the PRD for changed user flows, P0/P1 scope, product invariants, safety rules, data ownership, acceptance outcomes, release scope, or significant cost.

## Small-task bypass

For a local, reversible change with clear acceptance and no cross-boundary risk, bypass the full product lifecycle. Do not manufacture a PRD to justify ordinary maintenance.
