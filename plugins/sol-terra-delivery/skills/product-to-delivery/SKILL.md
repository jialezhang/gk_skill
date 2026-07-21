---
name: product-to-delivery
description: Use when a user wants to take product intent through approved artifacts and verified delivery, or needs the next valid stage after a pause or restart.
---

# Product to Delivery

Act as the lifecycle controller, not as a second delivery runtime.

Read these references completely before routing a stage:

- [references/lifecycle-contract.md](references/lifecycle-contract.md)
- [references/stage-routing.md](references/stage-routing.md)
- [references/approval-protocol.md](references/approval-protocol.md)
- [references/model-routing-contract.md](references/model-routing-contract.md)

## Route the current stage

1. Inspect existing artifacts before deciding the stage. Never restart discovery merely because the task changed agent or session.
2. If product intent is unclear, explicitly invoke the installed `$grill-me` skill. If unavailable, conduct equivalent focused discovery. Do not design implementation yet.
3. When discovery is sufficient, invoke `$create-product-prd` with a Sol-class product agent.
4. Stop after `REVIEW_REQUIRED`. Continue only after explicit approval of the exact PRD revision.
5. Invoke `$assess-goal-scope` before implementation planning. A P80 above 8 hours triggers a split discussion; a P80 above 10 hours triggers a strong recommendation. If the user-input mechanism supports auto-resolution, wait 240 seconds. Silence resolves only Goal packaging to `split_decision: single_goal` with `decision_source: timeout_default_single`.
6. Invoke `$create-implementation-plan` with a Sol-class planner and the validated scope decision. A split decision creates one program baseline and 2–3 bounded Goal plans; a single decision creates one Goal plan.
7. Stop after `PLAN_REVIEW_REQUIRED`. Continue only after explicit approval of the exact plan/tasks revisions.
8. Run the Sol/Terra/Luna model-routing Canary before formal execution. Do not start implementation when actual per-turn routing is unverified.
9. Invoke `$goal-driven-delivery` once per approved Goal. Each Goal receives its own visible session, worktree, branch, state, and checkpoint sequence. One program controller owns the cross-Goal dependency graph and Agent budget.
10. When multiple Goals finish, invoke `$integrate-goals` to merge them in an integration worktree and verify a clean integration commit.
11. Invoke `$review-delivery-gate` for evidence gates, final acceptance, and plan conflicts using the least costly model allowed by the routing contract.
12. If a PRD or plan revision invalidates approval, return to the owning stage rather than patching around it.

## Authority

- Product decisions belong to the user.
- PRD, scope judgment, architecture baseline, and high-risk plan revision belong to Sol-class agents.
- Runtime scheduling, implementation, debugging, integration, and retries belong to Terra controllers and executors.
- Routine evidence execution, browser E2E, build checks, checklist review, and routine final acceptance belong to Luna.
- One program controller owns program truth; each Goal controller owns only its Goal state.

Never infer approval from silence, earlier discussion, or a model's confidence.

## Model routing

Use explicit model selection on thread creation and on every follow-up turn:

- product discovery, PRD, scope assessment, implementation planning, architecture/plan contradiction, and high-risk security judgment: `gpt-5.6-sol`;
- delivery control, implementation, debugging, local rework, and integration: `gpt-5.6-terra`;
- focused checks, build, checklist review, browser E2E, evidence collection, and routine final acceptance: `gpt-5.6-luna`.

Read actual `turn_context.payload.model` metadata from the runtime rollout after every turn. Append the thread/turn identity, explicit-request fact, requested model, runtime-observed model, observation source, phase, and verification status to `model-routing.jsonl`. Validate the log against the raw rollout rather than trusting its copied `observed_model`. A mismatch returns `MODEL_ROUTE_MISMATCH`, invalidates that turn's output as delivery evidence, and stops dependent work. Never accept an agent name, prompt claim, UI label, or self-report as model evidence.

The live Canary requires an initial and an explicit-model follow-up turn for each model, plus the same-thread sequence Terra → Luna → Sol → Terra. A missing follow-up, unknown task class, unavailable rollout turn, or implicit model request blocks formal execution.

Use a fresh reviewer context when independence matters. Sol is an escalation path, not the default verifier.

## Recovery

On resume or context compaction, reconstruct current state from approved artifact revisions and `delivery-state.yaml`. Do not trust an earlier narrative summary when it conflicts with durable state or repository evidence.
