---
name: goal-driven-delivery
description: Use when an approved Goal plan is ready for implementation, recovery, or checkpointed verification after scope and model-routing preflight have passed.
---

# Goal-driven Delivery

Read these references completely before starting:

- [references/orchestration-contract.md](references/orchestration-contract.md)
- [references/state-machine.md](references/state-machine.md)
- [references/execution-packets.md](references/execution-packets.md)
- [references/escalation-loop.md](references/escalation-loop.md)
- [references/verification-loop.md](references/verification-loop.md)
- [references/checkpoint-contract.md](references/checkpoint-contract.md)

## Preconditions

Require all of:

- `prd_status: APPROVED`;
- `plan_status: PLAN_APPROVED` and matching PRD version;
- `tasks_status: PLAN_APPROVED` and matching plan version;
- a defined exact target, rollback path, gates, and completion criteria;
- a validated scope assessment and selected Goal boundary;
- a passing Sol/Terra/Luna routing Canary;
- explicit user authorization to execute and use subagents.

Return `DELIVERY_NOT_READY` if any condition is missing. Do not repair approval metadata implicitly.

## Start

1. Create or resume one visible session for this approved Goal. Do not set a token budget unless the user explicitly supplied one.
2. Use a dedicated worktree and branch for the Goal. Allocate an isolated development port/browser context when runtime verification is required; do not claim another Goal's runtime as exact-target evidence.
3. Run preflight: verify clean artifact revisions, repository target, worktree/branch, ports, rollback, verification commands, protected-data boundaries, program Agent budget, and absence of a second controller for this Goal.
4. Initialize `delivery-state.yaml` from [assets/delivery-state-template.yaml](assets/delivery-state-template.yaml), pin artifact/scope revisions, and register every task, gate, checkpoint, Goal session, worktree, and model-routing log before spawning work.
5. If the current agent is not the configured Terra controller, create one persistent Terra implementation context. Pass `gpt-5.6-terra` explicitly at creation and on every follow-up turn. Record the observed model in `model-routing.jsonl`; fail closed on mismatch.

## Agent budget

The program owns one cumulative budget across all Goals: normal target 8, soft limit 12, and a hard limit of 20 spawned child Agents. Maximum nesting depth is 1 and maximum parallel Goal sessions is 3.

- Reuse the same Terra implementer for local fixes and the same Luna verifier for routine evidence.
- Do not create one Agent per task, verifier-of-verifier chains, or recursive orchestration.
- At 12, stop spawning optional reviewers and consolidate remaining work.
- At 20, reject every further spawn with `AGENT_BUDGET_EXHAUSTED`; do not reset the count per Goal or after an Agent exits.

## Delivery loop

1. Re-read Goal, approved revisions, repository state, and delivery state. Reconcile abandoned/running attempts before selecting work.
2. Compute the ready queue from dependencies and gates; do not trust task ordering in prose.
3. Select tasks whose write scopes and consumed contracts do not conflict. Prefer one owner for coupled vertical work over artificial frontend/backend parallelism.
4. Reuse or spawn the preferred executor with explicit file/responsibility ownership and available program budget. Implementation, debugging, local rework, and integration use `gpt-5.6-terra`.
5. Give each executor only the current execution packet: global MUST/FORBIDDEN IDs, task, consumed contract revisions, relevant prior evidence, write scope, verification, and escalation rules.
6. Require the executor to inspect actual code before editing, implement the smallest complete task outcome, run focused checks, inspect its diff, and return [assets/handoff-template.yaml](assets/handoff-template.yaml).
7. Reject handoffs that omit artifact revisions, actual verification output, deviations, or remaining risk.
8. Assign routine focused checks, build, browser E2E, and checklist reconciliation to an independent `gpt-5.6-luna` context. Sol is used only for an allowed product, plan, architecture, or high-risk security escalation.
9. Route results:
   - local failure → same executor or debugger;
   - cross-module integration failure → integration executor;
   - plan contradiction → pause affected tasks and invoke `$review-delivery-gate` with a Sol escalation packet;
   - product conflict → stop affected delivery and request user decision.
10. At each gate invoke `$review-delivery-gate` with exact evidence. Never let task completion implicitly pass a gate.
11. When an independently runnable vertical slice or planned stage is complete, run the checkpoint contract: focused verification, diff/protected-data checks, commit only owned files, push the Goal branch, then issue a progress report with the commit SHA and four fixed denominators. A checkpoint is not delivered if commit or push failed.
12. Update state and `model-routing.jsonl` after every turn, attempt, review, gate, checkpoint, revision, and invalidation. Preserve history; do not overwrite failed evidence.
13. Continue until all blocking requirements reach `Verified` on the exact target and Luna routine final acceptance passes on a clean commit, or an allowed Sol escalation is resolved.

## Recovery and persistence

- On continuation, inspect live agents before declaring an attempt abandoned.
- Reconcile repository changes with recorded attempt/worktree ownership.
- If artifact revisions changed, pause and run invalidation analysis before resuming.
- If the Goal remains active and safe work remains, continue; do not stop at a narrative checkpoint.
- Mark blocked only after the applicable Goal policy and repeated-blocker threshold are satisfied.

## Completion

Mark the Goal complete only after `TARGET_VERIFIED` is attached to the exact clean commit, every required checkpoint is pushed/reported, model routing validates, and there is no required work remaining. A multi-Goal program remains incomplete until `$integrate-goals` verifies the integrated clean commit.
