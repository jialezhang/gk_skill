---
name: goal-driven-delivery
description: Execute an explicitly approved PRD and implementation plan through one persistent top-level Goal using a Terra delivery controller, bounded specialist subagents, independent verification, structured handoffs, plan-conflict escalation to Sol, and exact-target completion. Use only after both approval gates pass.
---

# Goal-driven Delivery

Read these references completely before starting:

- [references/orchestration-contract.md](references/orchestration-contract.md)
- [references/state-machine.md](references/state-machine.md)
- [references/execution-packets.md](references/execution-packets.md)
- [references/escalation-loop.md](references/escalation-loop.md)
- [references/verification-loop.md](references/verification-loop.md)

## Preconditions

Require all of:

- `prd_status: APPROVED`;
- `plan_status: PLAN_APPROVED` and matching PRD version;
- `tasks_status: PLAN_APPROVED` and matching plan version;
- a defined exact target, rollback path, gates, and completion criteria;
- explicit user authorization to execute and use subagents.

Return `DELIVERY_NOT_READY` if any condition is missing. Do not repair approval metadata implicitly.

## Start

1. Create one thread-level Goal for the approved product outcome. Do not set a token budget unless the user explicitly supplied one.
2. Run preflight: verify clean artifact revision matching, repository target, available roles/tools, rollback, verification commands, destructive boundaries, and absence of another active delivery controller.
3. Initialize `delivery-state.yaml` from [assets/delivery-state-template.yaml](assets/delivery-state-template.yaml), pin artifact revisions, and register every task and gate before spawning work.
4. If the current agent is not the configured Terra controller, spawn one persistent `terra_delivery` subagent with model `gpt-5.6-terra` and reasoning effort `high`. Give it the approved artifacts, state path, authority boundaries, and ready queue. Keep all live task truth in `delivery-state.yaml`.

## Delivery loop

1. Re-read Goal, approved revisions, repository state, and delivery state. Reconcile abandoned/running attempts before selecting work.
2. Compute the ready queue from dependencies and gates; do not trust task ordering in prose.
3. Select tasks whose write scopes and consumed contracts do not conflict. Prefer one owner for coupled vertical work over artificial frontend/backend parallelism.
4. Spawn the preferred executor role with explicit file/responsibility ownership. Default implementation model: `gpt-5.6-terra`, reasoning `high`.
5. Give each executor only the current execution packet: global MUST/FORBIDDEN IDs, task, consumed contract revisions, relevant prior evidence, write scope, verification, and escalation rules.
6. Require the executor to inspect actual code before editing, implement the smallest complete task outcome, run focused checks, inspect its diff, and return [assets/handoff-template.yaml](assets/handoff-template.yaml).
7. Reject handoffs that omit artifact revisions, actual verification output, deviations, or remaining risk.
8. Assign independent verification to an agent that did not author the change. Verification owns evidence; Sol owns product/gate judgment.
9. Route results:
   - local failure → same executor or debugger;
   - cross-module integration failure → integration executor;
   - plan contradiction → pause affected tasks and invoke `$review-delivery-gate` with a Sol escalation packet;
   - product conflict → stop affected delivery and request user decision.
10. At each gate invoke `$review-delivery-gate` with exact evidence. Never let task completion implicitly pass a gate.
11. Update state after every attempt, review, gate, revision, and invalidation. Preserve history; do not overwrite failed evidence.
12. Continue until all blocking requirements reach `Verified` on the exact target and final Sol review passes.

## Recovery and persistence

- On continuation, inspect live agents before declaring an attempt abandoned.
- Reconcile repository changes with recorded attempt ownership.
- If artifact revisions changed, pause and run invalidation analysis before resuming.
- If the Goal remains active and safe work remains, continue; do not stop at a narrative checkpoint.
- Mark blocked only after the applicable Goal policy and repeated-blocker threshold are satisfied.

## Completion

Mark the Goal complete only after final Sol acceptance establishes `TARGET_VERIFIED` and there is no required work remaining. Never mark complete because all original checkboxes are checked.
