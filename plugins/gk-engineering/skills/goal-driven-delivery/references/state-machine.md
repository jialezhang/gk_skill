# Delivery State Machine

## Task states

```text
pending → ready → assigned → in_progress → implemented
→ verification_pending → verified → complete
```

Exceptional transitions:

- `in_progress → needs_rework → ready`
- `in_progress → plan_conflict`
- `assigned/in_progress → abandoned → ready` after agent-liveness reconciliation
- any nonterminal state → `blocked` for a genuine external/product blocker
- `implemented/verified → stale` when a consumed artifact revision changes
- `verified → stale` when its accepted evidence is invalidated, superseded, or its runtime provenance no longer identifies the verified target

Only the controller changes task state. Executors report outcomes; they do not mark shared state complete.

## Gate states

`pending → review_ready → passed | failed | blocked | stale`

A gate becomes `review_ready` only when all prerequisites and required evidence are present. A gate becomes `passed` only when every referenced record is `accepted`; runtime targets additionally require same-candidate verified runtime provenance. Plan revision marks dependent passed gates `stale` when their proof no longer applies.

## Attempt identity

Each assignment creates a unique attempt containing Goal/session/worktree, task ID, artifact revisions, requested and observed model, executor role/agent, write scope, start/end time, result, commits/diff identity, tests, evidence, deviations, and invalidation status.

Every completed checkpoint records a clean commit SHA, verified remote push, fixed-denominator progress report, model-routing validation, and any evidence lifecycle transition. A checkpoint without the first four remains `checkpoint_incomplete`.

## Artifact pinning

State pins PRD, plan, tasks, and verification revisions. The controller must not execute a packet generated from another revision. Approval metadata and content revision travel together.

## Terminal telemetry

Before a Goal transitions to `complete` or `blocked`, the controller captures a completion telemetry snapshot. The snapshot records its capture time, source, observed totals by model/stage where available, and explicit unavailable fields. A terminal state without a pre-transition snapshot is invalid because many runtimes no longer expose Goal usage after completion.

## Completion transaction

`GOAL_TARGET_VERIFIED` and `PROGRAM_TARGET_VERIFIED` are verified pre-terminal states. The controller issues a completion receipt only while both states, the candidate, Profile, routing log, raw rollout files, telemetry, and optional integration manifest still match. The receipt records SHA-256 digests for every input. State-file digests normalize only the fields changed by the terminal transition; candidate, Profile, evidence, routing or other state changes still invalidate the receipt.

Before transitioning either state to `COMPLETE`, revalidate the receipt against the current files, then persist the receipt path and digest in both states. Any changed or missing input invalidates the receipt and returns delivery to the relevant verification state. `COMPLETE` without a ready receipt is invalid for current schemas.
