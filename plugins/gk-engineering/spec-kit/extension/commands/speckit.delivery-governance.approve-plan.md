---
description: Record explicit user approval of the implementation plan and tasks baseline.
---

## User Input

```text
$ARGUMENTS
```

## Procedure

1. Resolve the active feature directory and read `spec.md`, `plan.md`, `tasks.md`, and `verification.md` when present.
2. Require direct evidence that the user approved these exact revisions, either in the current user message or the immediately preceding workflow gate.
3. Confirm the PRD is `APPROVED`; plan/tasks reference its exact version; requirement traceability, dependency graph, gates, rollback, escalation, and exact-target cases are complete; and no blocking consistency finding remains.
4. Update only approval metadata:
   - `plan_status: PLAN_APPROVED`
   - `tasks_status: PLAN_APPROVED`
   - `approved_by: user`
   - `approved_at: <current ISO-8601 timestamp>`
5. Do not change technical content while approving. If the baseline needs revision, retain `PLAN_REVIEW_REQUIRED` and report the owning section.
6. Return approved paths and revision IDs.
