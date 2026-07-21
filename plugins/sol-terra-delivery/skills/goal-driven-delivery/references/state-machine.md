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

Only the controller changes task state. Executors report outcomes; they do not mark shared state complete.

## Gate states

`pending → review_ready → passed | failed | blocked | stale`

A gate becomes `review_ready` only when all prerequisites and required evidence are present. Plan revision marks dependent passed gates `stale` when their proof no longer applies.

## Attempt identity

Each assignment creates a unique attempt containing task ID, artifact revisions, executor role/agent, write scope, start/end time, result, commits/diff identity, tests, evidence, deviations, and invalidation status.

## Artifact pinning

State pins PRD, plan, tasks, and verification revisions. The controller must not execute a packet generated from another revision. Approval metadata and content revision travel together.
