---
description: Reconcile the current product, planning, delivery, gate, and verification states.
---

## Procedure

1. Resolve the active feature directory.
2. Read `spec.md`, `scope-assessment.yaml`, program/Goal `plan.md`, `tasks.md`, `verification.md`, `delivery-state.yaml`, `model-routing.jsonl`, and `program-integration.json` when present.
3. Report exact artifact versions and approvals; P50/P80/P90 and split decision source; Goal/session/worktree states; Agent budget; model-routing validity; checkpoint commit/push/report coverage; integration state; task/gate counts; stale attempts; open escalations; and next valid action.
4. Flag version mismatches and illegal transitions. An approved plan may not consume an unapproved or different PRD revision.
5. Distinguish `Implemented`, `Enabled`, `Executed`, `Verified`, and `Complete`.
6. Do not modify product or implementation files.
