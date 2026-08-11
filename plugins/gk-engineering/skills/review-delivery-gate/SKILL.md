---
name: review-delivery-gate
description: Use when delivery reaches an evidence gate, encounters a plan-level contradiction, or needs exact-target acceptance on a pinned clean commit.
---

# Review Delivery Gate

Keep review read-only except for approved plan/state/decision artifacts. Choose the model by review class and pass it explicitly on every turn:

- deterministic focused tests, typecheck, build, diff, baseline comparison, checklist review, and
  evidence reconciliation: prefer `gpt-5.6-luna`; if unavailable, use the current model under
  `luna_route_fallback`;
- implementation-quality review, browser acceptance, 阶段真实用户旅程,
  runtime/provider-boundary acceptance, and final exact-target acceptance: prefer
  `gpt-5.6-terra`; after three failed raw route attempts use `terra_route_fallback`;
- product decisions, plan/architecture contradictions, or high-risk security judgment: prefer `gpt-5.6-sol`; if unavailable, the current model continues under `sol_route_fallback`.

For every browser-related acceptance path, Terra must operate the page exclusively through Ego Lite `ego-browser` and follow [../goal-driven-delivery/references/browser-acceptance-contract.md](../goal-driven-delivery/references/browser-acceptance-contract.md). Playwright, Chrome control, generic computer-use, built-in browser tools, and manual browser claims are not acceptance evidence.

Run the no-write model handshake before review work. Bind native review to the raw controller spawn
call and child runtime model. A route-guard nonce is optional supplemental evidence.
`MODEL_ROUTE_MISMATCH` or a missing raw handshake invalidates the review and quarantines its output.

Gate review may identify a PRD or plan conflict. Perform artifact modification through the owning PRD or implementation-planning stage.

Read these references completely:

- [references/review-contract.md](references/review-contract.md)
- [references/gate-protocol.md](references/gate-protocol.md)
- [references/plan-revision.md](references/plan-revision.md)
- [references/final-acceptance.md](references/final-acceptance.md)

## Review

### Prepare

1. Pin PRD, plan, tasks, verification, build, target, and evidence revisions.
2. Require a clean commit for final acceptance. A dirty worktree may provide diagnostics but cannot receive `TARGET_VERIFIED`.
3. Confirm final acceptance runs in a fresh Terra or audited Terra-fallback thread that did not
   author the implementation and receives raw candidate evidence.
4. Reject incomplete packets before evaluating quality; missing evidence is not a passing inference.
5. Reuse valid same-candidate evidence. Do not rerun a check merely because the reviewer changed; rerun only when the candidate or a declared invalidation key changed.

### Evaluate

1. Compare observable outcomes with PRD journeys and invariants before checking task compliance.
2. Verify exact target identity, focused checks, integration boundaries, runtime evidence, rollback, safety, data ownership, migration, and Legacy obligations required by the gate.
3. Inspect actual diff and repository state for unplanned architecture, scope, duplicate ownership, and fallback substitutions.
4. Classify each finding as `local_rework`, `plan_conflict`, `product_decision_required`, or `verification_blocked`, with severity and owning artifact.

### Decide

1. For local rework, return precise task/evidence requirements to Terra without redesigning the plan.
2. For a plan conflict, return the evidence packet to the planning stage, preferring Sol and otherwise continuing on the current model under `sol_route_fallback`; revise only the affected technical baseline/tasks, increment the plan version, record decisive evidence, and identify invalidated attempts/gates.
3. For a product conflict, present the user with the minimum decision set, product consequences, and recommended option; do not approve a downgrade silently.
4. Return one verdict: `GATE_PASSED`, `REWORK_REQUIRED`, `PLAN_REVISED`, `PRODUCT_DECISION_REQUIRED`, `VERIFICATION_BLOCKED`, or `TARGET_VERIFIED`.
5. Persist the verdict and evidence references in delivery state/decision log before Terra resumes.

Only `TARGET_VERIFIED` on the pinned clean commit, raw-runtime-validated model-routing records, and
no remaining required work permits a single Goal to reach `GOAL_TARGET_VERIFIED`. For a multi-Goal
Program, this is a milestone and cannot close the Program. Only an independent Terra or audited
Terra-fallback final-acceptance thread may issue the final `TARGET_VERIFIED` verdict. Before runtime
Program completion, require the plugin-root `scripts/validate_completion_gate.py` composite result;
copied status fields and model labels are insufficient.
