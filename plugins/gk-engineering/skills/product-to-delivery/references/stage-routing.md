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
| Technical-change candidate, no PRD decision | ask whether PRD is needed; include a recommendation and rationale |
| User chooses `PRD_NOT_REQUIRED` | record the choice and enter the technical-change lane |
| User chooses `PRD_REQUIRED`, no PRD | run `create-product-prd` |
| Request crosses a governed product boundary, no PRD | explain why a PRD is required, then run `create-product-prd` |
| PRD `DRAFT` or `CHANGE_REQUESTED` | revise PRD |
| PRD `REVIEW_REQUIRED` | wait for user approval |
| PRD `APPROVED`, no matching scope assessment | `assess-goal-scope` |
| Scope split decision pending | ask user; after 240 seconds default to one Goal |
| Scope decision recorded, no matching plan | run `create-implementation-plan` |
| Plan `READINESS_BLOCKED` | Prefer Sol to gather missing technical evidence; if unavailable, current model continues under `sol_route_fallback` |
| Plan `PLAN_REVIEW_REQUIRED` | wait for user approval |
| Plan `PLAN_APPROVED`, Canary missing | run and verify Sol/Terra/Luna routing Canary; evidenced role-specific current-model fallback is non-blocking |
| Single-Goal plan approved, no active delivery | `goal-driven-delivery` |
| Multi-Goal program approved | create one runtime Program Goal and `program-state.yaml`, then start bounded Goal sessions/worktrees by dependency wave |
| Delivery active, local failure | Terra repair loop |
| Delivery active, plan contradiction | perform the plan review/revision, preferring Sol and otherwise using `sol_route_fallback` |
| Delivery active, product conflict | user decision |
| Goal checkpoint complete | commit, push, and progress report |
| All Goals are `GOAL_TARGET_VERIFIED` | `integrate-goals` in a clean integration worktree |
| Integrated target appears done | independent Terra or audited Terra-fallback exact-target acceptance; Sol only on allowed escalation |
| Same-candidate completion receipt issued and revalidated | persist its digest, transition states to `COMPLETE`, then complete the runtime Program Goal |
| Program Goal is `COMPLETE`, receipt captured, retrospective missing | invoke `goal-retrospective` once for the Program and write the auditable retrospective |
| Retrospective write failed after valid completion | report `RETROSPECTIVE_PENDING` with the exact evidence gap and recovery action; do not rewrite Goal status |

## Stage invariants

- Do not infer `PRD_NOT_REQUIRED` from silence, task size, or the absence of a Spec Kit feature.
- Do not invoke `assess-goal-scope` from the technical-change lane.
- Do not invoke `create-implementation-plan` from the technical-change lane.
- Do not invoke `goal-driven-delivery` from the technical-change lane; those skills validate a governed PRD/plan lifecycle.
- Keep technical-change planning lightweight and proportionate: pin the objective, constraints, affected boundary, acceptance checks, and rollback when relevant, then inspect, edit, test, and verify directly.
- If implementation evidence reveals a user-visible outcome, public-contract, safety/compliance, data-ownership, release-scope, or significant-cost change, stop the technical-change lane and reclassify the task before continuing.
- Do not generate a governed plan from an unapproved PRD.
- Do not create a Goal from an unapproved plan.
- Do not let approval survive a material content revision without explicit reapproval.
- Do not let Spec Kit Workflow and native Goal delivery both schedule implementation.
- Do not complete a runtime Program Goal when only one Goal or checkpoint is verified.
- Do not invoke the automatic retrospective before the runtime Program Goal is complete and its completion receipt is captured.
- Do not use a retrospective as acceptance evidence, infer missing statistics, or reopen a valid completion solely because the retrospective write failed.
- Do not manufacture a retrospective for the technical-change lane when no runtime Goal exists; invoke it there only when the user explicitly requests a retrospective for an identifiable Goal.
- Do not ask the user to decide discoverable technical facts.
- Preferred model unavailability never blocks Goal work by itself. Preserve ownership and
  independence, use the current model, and record complete role-specific fallback evidence; Terra
  fallback additionally requires three failed raw route attempts.
