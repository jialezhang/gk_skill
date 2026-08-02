# Review Contract

## Evidence packet

Require the approved artifact versions, affected task/gate IDs, repository diff, focused and regression results, real runtime evidence, deviations, current delivery state, and escalation packet when applicable.

## Finding ownership

- `local_rework`: implementation does not satisfy an unchanged task contract; return to Terra.
- `plan_conflict`: repository/runtime evidence contradicts a technical baseline or dependency; return it to the current main agent, which revises the affected plan without delegation, preferring Sol and otherwise using `sol_route_fallback`.
- `product_decision_required`: any viable resolution changes approved product behavior, scope, invariant, safety, data ownership, completion, release scope, or significant cost; return options to the user.
- `verification_blocked`: implementation may exist but the approved target cannot be exercised or evidenced.

## Model boundary

Luna owns deterministic low-complexity checks against already approved criteria. Terra owns local code-quality review, browser and 阶段真实用户旅程 execution, runtime/Provider judgment, repair advice, and final acceptance. Every browser operation is exclusive to Ego Lite `ego-browser`. Sol is preferred only for product, plan, architecture, or high-risk security judgment; if unavailable, the current model continues under `sol_route_fallback`. The presence of a final gate does not by itself justify Sol.

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
- accepted worktree clean and pinned to the recorded pushed commit;
- model-routing records valid for every review turn;
- completed checkpoints committed, pushed, and reported.

Final acceptance uses an independent Terra thread and valid same-candidate evidence. Return `TARGET_VERIFIED` only when every condition holds; escalate to the current main planning agent only if reconciliation exposes a product, plan, architecture, or high-risk security contradiction. Prefer Sol, but use `sol_route_fallback` when unavailable.
