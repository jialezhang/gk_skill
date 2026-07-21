---
name: review-delivery-gate
description: Perform a read-only Sol-class review of an implementation gate, plan conflict, plan revision, or final product acceptance. Use when delivery reaches a defined gate, runtime evidence contradicts the approved baseline, or all tasks appear complete and the exact product target must be reconciled against the PRD.
---

# Review Delivery Gate

Use a Sol-class reviewer with model `gpt-5.6-sol` and reasoning effort `xhigh` when the current agent is not already equivalent. Keep the review read-only except for approved plan/state/decision artifacts.

Read these references completely:

- [references/review-contract.md](references/review-contract.md)
- [references/gate-protocol.md](references/gate-protocol.md)
- [references/plan-revision.md](references/plan-revision.md)
- [references/final-acceptance.md](references/final-acceptance.md)

## Review

### Prepare

1. Pin PRD, plan, tasks, verification, build, target, and evidence revisions.
2. Confirm the reviewer did not author the implementation being accepted. When the same model family is used, require a fresh context and raw evidence.
3. Reject incomplete packets before evaluating quality; missing evidence is not a passing inference.

### Evaluate

1. Compare observable outcomes with PRD journeys and invariants before checking task compliance.
2. Verify exact target identity, focused checks, integration boundaries, runtime evidence, rollback, safety, data ownership, migration, and Legacy obligations required by the gate.
3. Inspect actual diff and repository state for unplanned architecture, scope, duplicate ownership, and fallback substitutions.
4. Classify each finding as `local_rework`, `plan_conflict`, `product_decision_required`, or `verification_blocked`, with severity and owning artifact.

### Decide

1. For local rework, return precise task/evidence requirements to Terra without redesigning the plan.
2. For a plan conflict, revise only affected technical baseline/tasks, increment the plan version, record decisive evidence, and identify invalidated attempts/gates.
3. For a product conflict, present the user with the minimum decision set, product consequences, and recommended option; do not approve a downgrade silently.
4. Return one verdict: `GATE_PASSED`, `REWORK_REQUIRED`, `PLAN_REVISED`, `PRODUCT_DECISION_REQUIRED`, `VERIFICATION_BLOCKED`, or `TARGET_VERIFIED`.
5. Persist the verdict and evidence references in delivery state/decision log before Terra resumes.

Only `TARGET_VERIFIED` plus no remaining required work permits Goal completion.
