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
| PRD `APPROVED`, no matching scope assessment | `assess-goal-scope` |
| Scope split decision pending | ask user; after 240 seconds default to one Goal |
| Scope decision recorded, no matching plan | `create-implementation-plan` |
| Plan `READINESS_BLOCKED` | Sol gathers missing technical evidence |
| Plan `PLAN_REVIEW_REQUIRED` | wait for user approval |
| Plan `PLAN_APPROVED`, Canary missing | run and verify Sol/Terra/Luna routing Canary |
| Single-Goal plan approved, no active delivery | `goal-driven-delivery` |
| Multi-Goal program approved | start bounded Goal sessions/worktrees by dependency wave |
| Delivery active, local failure | Terra repair loop |
| Delivery active, plan contradiction | Sol plan review/revision |
| Delivery active, product conflict | user decision |
| Goal checkpoint complete | commit, push, and progress report |
| All Goals complete | `integrate-goals` in a clean integration worktree |
| Integrated target appears done | Luna routine final acceptance; Sol only on allowed escalation |

## Stage invariants

- Do not generate a plan from an unapproved PRD.
- Do not create a Goal from an unapproved plan.
- Do not let approval survive a material content revision without explicit reapproval.
- Do not let Spec Kit Workflow and native Goal delivery both schedule implementation.
- Do not ask the user to decide discoverable technical facts.
