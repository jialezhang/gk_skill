---
name: product-to-delivery
description: Orchestrate an approved product-development lifecycle across discovery, PRD creation, implementation planning, Goal-driven multi-agent delivery, escalation, and final verification. Use when a user wants the complete Sol-planning/Terra-delivery workflow or asks what stage to run next; pause at PRD and plan approvals.
---

# Product to Delivery

Act as the lifecycle controller, not as a second delivery runtime.

Read these references completely before routing a stage:

- [references/lifecycle-contract.md](references/lifecycle-contract.md)
- [references/stage-routing.md](references/stage-routing.md)
- [references/approval-protocol.md](references/approval-protocol.md)

## Route the current stage

1. Inspect existing artifacts before deciding the stage. Never restart discovery merely because the task changed agent or session.
2. If product intent is unclear, explicitly invoke the installed `$grill-me` skill. If unavailable, conduct equivalent focused discovery. Do not design implementation yet.
3. When discovery is sufficient, invoke `$create-product-prd` with a Sol-class product agent.
4. Stop after `REVIEW_REQUIRED`. Continue only after explicit approval of the exact PRD revision.
5. Invoke `$create-implementation-plan` with a Sol-class planner.
6. Stop after `PLAN_REVIEW_REQUIRED`. Continue only after explicit approval of the exact plan/tasks revisions.
7. Invoke `$goal-driven-delivery`. Create the sole top-level Goal only in this stage.
8. Invoke `$review-delivery-gate` at defined gates, on plan-level contradictions, and for final acceptance.
9. If a PRD or plan revision invalidates approval, return to the owning stage rather than patching around it.

## Authority

- Product decisions belong to the user.
- PRD, architecture baseline, plan revision, gate review, and final acceptance belong to Sol-class agents.
- Runtime scheduling, implementation, retries, and evidence collection belong to the Terra delivery controller and its bounded executors.
- Only one delivery controller may own live task state.

Never infer approval from silence, earlier discussion, or a model's confidence.

## Model routing

When the caller has not already selected an equivalent model:

- discovery, PRD, planning, plan revision, gate review, and final acceptance: spawn `gpt-5.6-sol` with `xhigh` reasoning;
- delivery control and implementation: spawn `gpt-5.6-terra` with `high` reasoning;
- use a separate reviewer context from the author whenever a quality gate depends on independent criticism.

Model names are defaults, not product artifacts. Preserve role authority if configuration maps the roles to newer models.

## Recovery

On resume or context compaction, reconstruct current state from approved artifact revisions and `delivery-state.yaml`. Do not trust an earlier narrative summary when it conflicts with durable state or repository evidence.
