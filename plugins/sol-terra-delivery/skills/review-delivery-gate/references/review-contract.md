# Review Contract

## Evidence packet

Require the approved artifact versions, affected task/gate IDs, repository diff, focused and regression results, real runtime evidence, deviations, current delivery state, and escalation packet when applicable.

## Finding ownership

- `local_rework`: implementation does not satisfy an unchanged task contract; return to Terra.
- `plan_conflict`: repository/runtime evidence contradicts a technical baseline or dependency; Sol revises the affected plan.
- `product_decision_required`: any viable resolution changes approved product behavior, scope, invariant, safety, data ownership, completion, release scope, or significant cost; return options to the user.
- `verification_blocked`: implementation may exist but the approved target cannot be exercised or evidenced.

## Plan revision rules

Do not rewrite unaffected tasks. Record the old and new decision, evidence, impact, invalidated attempts, new plan version, and the gate that must be rerun. Preserve prior evidence as historical, not current, proof.

## Final acceptance

Check the PRD first, then the plan. Require:

- every blocking journey executed on the exact approved target;
- every P0/P1 outcome verified, not merely implemented or enabled;
- safety, authorization, data, migration, rollback, and compatibility obligations reconciled;
- no fallback, fixture, legacy path, or adjacent capability presented as target evidence;
- no required task, gate, escalation, or plan revision left open;
- remaining non-blocking risks explicitly documented.

Return `TARGET_VERIFIED` only when every condition holds.
