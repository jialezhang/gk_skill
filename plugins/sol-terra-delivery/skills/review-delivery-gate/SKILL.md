---
name: review-delivery-gate
description: Use when delivery reaches an evidence gate, encounters a plan-level contradiction, or needs exact-target acceptance on a pinned clean commit.
---

# Review Delivery Gate

Keep review read-only except for approved plan/state/decision artifacts. Choose the model by review class and pass it explicitly on every turn:

- focused checks, build/checklist review, browser E2E, ordinary evidence gates, and routine final acceptance: `gpt-5.6-luna`;
- local implementation-quality review that requires code reasoning: `gpt-5.6-terra`;
- product decisions, plan/architecture contradictions, or high-risk security judgment: `gpt-5.6-sol`.

Record and validate actual per-turn model metadata. `MODEL_ROUTE_MISMATCH` invalidates the review.

Read these references completely:

- [references/review-contract.md](references/review-contract.md)
- [references/gate-protocol.md](references/gate-protocol.md)
- [references/plan-revision.md](references/plan-revision.md)
- [references/final-acceptance.md](references/final-acceptance.md)

## Review

### Prepare

1. Pin PRD, plan, tasks, verification, build, target, and evidence revisions.
2. Require a clean commit for final acceptance. A dirty worktree may provide diagnostics but cannot receive `TARGET_VERIFIED`.
3. Confirm the reviewer did not author the implementation being accepted. When the same model family is used, require a fresh context and raw evidence.
4. Reject incomplete packets before evaluating quality; missing evidence is not a passing inference.

### Evaluate

1. Compare observable outcomes with PRD journeys and invariants before checking task compliance.
2. Verify exact target identity, focused checks, integration boundaries, runtime evidence, rollback, safety, data ownership, migration, and Legacy obligations required by the gate.
3. Inspect actual diff and repository state for unplanned architecture, scope, duplicate ownership, and fallback substitutions.
4. Classify each finding as `local_rework`, `plan_conflict`, `product_decision_required`, or `verification_blocked`, with severity and owning artifact.

### Decide

1. For local rework, return precise task/evidence requirements to Terra without redesigning the plan.
2. For a plan conflict, escalate to Sol, revise only affected technical baseline/tasks, increment the plan version, record decisive evidence, and identify invalidated attempts/gates.
3. For a product conflict, present the user with the minimum decision set, product consequences, and recommended option; do not approve a downgrade silently.
4. Return one verdict: `GATE_PASSED`, `REWORK_REQUIRED`, `PLAN_REVISED`, `PRODUCT_DECISION_REQUIRED`, `VERIFICATION_BLOCKED`, or `TARGET_VERIFIED`.
5. Persist the verdict and evidence references in delivery state/decision log before Terra resumes.

Only `TARGET_VERIFIED` on the pinned clean commit, valid model-routing records, and no remaining required work permits Goal completion. Luna may issue this verdict for routine final acceptance when no escalation-class contradiction exists.
