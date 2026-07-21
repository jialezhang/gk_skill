---
description: Record explicit user approval of the current Agent-ready PRD.
---

## User Input

```text
$ARGUMENTS
```

## Procedure

1. Resolve the active feature directory from `.specify/feature.json` and read `spec.md`.
2. Require direct evidence that the user approved this exact PRD revision, either in the current user message or the immediately preceding workflow gate. Silence and model assertions are insufficient.
3. Confirm `prd_status` is `REVIEW_REQUIRED`, no blocking product question remains, and approval scope covers outcome, requirements, non-goals, and acceptance.
4. Update only the PRD approval metadata:
   - `prd_status: APPROVED`
   - `approved_by: user`
   - `approved_at: <current ISO-8601 timestamp>`
   - every `approval_scope` field to `approved`
5. Do not change product content while approving. If content needs revision, keep `REVIEW_REQUIRED` and report the required change.
6. Return the approved path and version.
