---
name: review-delivery-gate
description: Use when delivery reaches an evidence gate, encounters a plan-level contradiction, or needs exact-target acceptance on a pinned clean commit.
---

# Review Delivery Gate

Keep review read-only except for approved plan/state/decision artifacts. Choose the model by review class and pass it explicitly on every turn:

- deterministic focused tests, typecheck, build, diff, baseline comparison, checklist review, and evidence reconciliation: `gpt-5.6-luna`;
- implementation-quality review, browser acceptance, 阶段真实用户旅程, runtime/provider-boundary acceptance, and final exact-target acceptance: `gpt-5.6-terra`;
- product decisions, plan/architecture contradictions, or high-risk security judgment: `gpt-5.6-sol`.

Run the no-write model handshake before review work. Record and validate actual per-turn model metadata. `MODEL_ROUTE_MISMATCH` or a missing handshake invalidates the review and quarantines its output.

Gate review may identify a PRD or plan conflict, but artifact modification is non-delegable: the current main agent must perform every PRD or implementation-plan revision. Do not spawn, create, or delegate a child agent, subagent, separate reviewer context, or separate task to make those revisions.

Read these references completely:

- [references/review-contract.md](references/review-contract.md)
- [references/gate-protocol.md](references/gate-protocol.md)
- [references/plan-revision.md](references/plan-revision.md)
- [references/final-acceptance.md](references/final-acceptance.md)

## Review

### Prepare

1. Pin PRD, plan, tasks, verification, build, target, and evidence revisions.
2. Require a clean commit for final acceptance. A dirty worktree may provide diagnostics but cannot receive `TARGET_VERIFIED`.
3. Confirm final acceptance runs in a fresh Terra thread that did not author the implementation and receives raw candidate evidence.
4. Reject incomplete packets before evaluating quality; missing evidence is not a passing inference.
5. Reuse valid same-candidate evidence. Do not rerun a check merely because the reviewer changed; rerun only when the candidate or a declared invalidation key changed.

### Evaluate

1. Compare observable outcomes with PRD journeys and invariants before checking task compliance.
2. Verify exact target identity, focused checks, integration boundaries, runtime evidence, rollback, safety, data ownership, migration, and Legacy obligations required by the gate.
3. Inspect actual diff and repository state for unplanned architecture, scope, duplicate ownership, and fallback substitutions.
4. Classify each finding as `local_rework`, `plan_conflict`, `product_decision_required`, or `verification_blocked`, with severity and owning artifact.

### Decide

1. For local rework, return precise task/evidence requirements to Terra without redesigning the plan.
2. For a plan conflict, return the evidence packet to the current main agent. The main agent enters the Sol planning stage, revises only the affected technical baseline/tasks, increments the plan version, records decisive evidence, and identifies invalidated attempts/gates.
3. For a product conflict, present the user with the minimum decision set, product consequences, and recommended option; do not approve a downgrade silently.
4. Return one verdict: `GATE_PASSED`, `REWORK_REQUIRED`, `PLAN_REVISED`, `PRODUCT_DECISION_REQUIRED`, `VERIFICATION_BLOCKED`, or `TARGET_VERIFIED`.
5. Persist the verdict and evidence references in delivery state/decision log before Terra resumes.

Only `TARGET_VERIFIED` on the pinned clean commit, raw-runtime-validated model-routing records, and no remaining required work permits a single Goal to reach `GOAL_TARGET_VERIFIED`. For a multi-Goal Program, this is a milestone and cannot close the Program. Only an independent Terra final-acceptance thread may issue the final `TARGET_VERIFIED` verdict. Before runtime Program completion, require the plugin-root `scripts/validate_completion_gate.py` composite result; copied status fields and model labels are insufficient.
