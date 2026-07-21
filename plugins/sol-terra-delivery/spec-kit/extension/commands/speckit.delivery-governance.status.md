---
description: Reconcile the current product, planning, delivery, gate, and verification states.
---

## Procedure

1. Resolve the active feature directory.
2. Read `spec.md`, `plan.md`, `tasks.md`, `verification.md`, and `delivery-state.yaml` when present.
3. Report the exact PRD, plan, and tasks versions; approval states; active Goal state; task/gate counts; stale attempts; open escalations; and next valid action.
4. Flag version mismatches and illegal transitions. An approved plan may not consume an unapproved or different PRD revision.
5. Distinguish `Implemented`, `Enabled`, `Executed`, `Verified`, and `Complete`.
6. Do not modify product or implementation files.
