# Stage Routing

## Artifact discovery order

1. Explicit paths in the user request.
2. Active Spec Kit feature metadata and feature directory.
3. Repository-defined product/plan conventions.
4. Current conversation only when no durable artifact exists.

## Routing table

| Evidence | Next stage |
| --- | --- |
| No discovery and intent materially ambiguous | `grill-me` |
| Discovery complete, no PRD | `create-product-prd` |
| PRD `DRAFT` or `CHANGE_REQUESTED` | revise PRD |
| PRD `REVIEW_REQUIRED` | wait for user approval |
| PRD `APPROVED`, no matching plan | `create-implementation-plan` |
| Plan `READINESS_BLOCKED` | Sol gathers missing technical evidence |
| Plan `PLAN_REVIEW_REQUIRED` | wait for user approval |
| Plan `PLAN_APPROVED`, no active delivery | `goal-driven-delivery` |
| Delivery active, local failure | Terra repair loop |
| Delivery active, plan contradiction | Sol plan review/revision |
| Delivery active, product conflict | user decision |
| All tasks appear done | independent verification then Sol final acceptance |

## Stage invariants

- Do not generate a plan from an unapproved PRD.
- Do not create a Goal from an unapproved plan.
- Do not let approval survive a material content revision without explicit reapproval.
- Do not let Spec Kit Workflow and native Goal delivery both schedule implementation.
- Do not ask the user to decide discoverable technical facts.
