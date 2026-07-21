---
prd_status: REVIEW_REQUIRED
prd_version: 0.1.0
approved_by: null
approved_at: null
approval_scope:
  product_outcome: pending
  requirements: pending
  non_goals: pending
  acceptance: pending
---

# PRD: [FEATURE NAME]

## Product Decision Summary

- **Decision**:
- **Why now**:
- **Alternatives rejected**:

## Product Outcome

- **Target user**: [Who]
- **Problem**: [Current pain]
- **Primary journey**: [Action and context]
- **User-visible result**: [Observable success]

## Evidence and Current Behavior

| Evidence | Source | Product implication |
| --- | --- | --- |

## Product Invariants

- **INV-001**: [Behavior or boundary that must remain true]

## Product Concepts and State Model

| Concept/state | Meaning | Entry condition | Exit/terminal condition | User-visible behavior |
| --- | --- | --- | --- | --- |

## Experience and Behavior Rules

- **UX-001**: [Stable interaction rule]

## Requirements

| ID | Priority | Requirement | Domain | Risk | Acceptance type | User decision if changed |
| --- | --- | --- | --- | --- | --- | --- |
| R-001 | P0 |  |  |  | real-target | required |

## Non-goals

- **NG-001**: [Explicit exclusion]

## Core Journeys

### J-001: [Journey name]

- Actor:
- Preconditions:
- Action:
- Observable success:
- Failure behavior:
- Edge conditions:

## Human Decision Boundary

### Delivery may decide

- Reversible internal implementation choices that preserve this contract.

### User approval is required

- Changes to P0/P1 behavior, invariants, non-goals, safety, authoritative data, completion, release scope, or significant cost.

## Implementation Freedom

- Internal module layout, naming, equivalent algorithms, test mechanics, and reversible refactors are implementation choices.

## Acceptance Inventory

| Journey | Level | Must prove | Target evidence | Blocking |
| --- | --- | --- | --- | --- |
| J-001 | core |  | real-target | yes |

## Success Metrics

| Metric | Baseline | Target | Measurement | Blocking |
| --- | --- | --- | --- | --- |

## Product Assumptions and Open Questions

### Approved assumptions

- None.

### Technical assumptions for planning

- None.

### Open product questions

- None.

## Rejected Options

| Option | Reason rejected | Reconsider when |
| --- | --- | --- |

## Release and Rollback Requirements

- Release scope:
- Rollback expectation:
- Data protection:

## Change Control

- **Plan-only changes**: Internal technical paths that preserve this PRD.
- **PRD revision required**: Product behavior, scope, invariants, safety, data ownership, completion, release scope, or significant cost.

## Completion Definition

- Every blocking journey is verified on the approved target.
- No P0/P1 requirement is merely implemented, enabled, or silently deferred.
- Remaining non-blocking gaps are explicit.
