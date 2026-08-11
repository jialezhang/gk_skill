# Orchestration Contract

## Single runtime owner

The program controller owns cross-Goal dependencies, cumulative Agent budget, and integration readiness. Each Terra Goal controller owns only its Goal's live state. Spec Kit artifacts are durable baselines, not a second scheduler. Revise PRDs or plans through their owning stage, preferring Sol and otherwise using the current model under `sol_route_fallback`; do not dispatch implementation while a revision is active.

## Role routing

| Work | Default role | Default model/effort |
| --- | --- | --- |
| Runtime scheduling and integration | `terra_delivery` | prefer `gpt-5.6-terra`; audited current-model fallback after three raw failures |
| Frontend implementation | `frontend_executor` | prefer `gpt-5.6-terra`; audited current-model fallback after three raw failures |
| Backend implementation | `backend_executor` | prefer `gpt-5.6-terra`; audited current-model fallback after three raw failures |
| Data/migration implementation | `data_executor` | prefer `gpt-5.6-terra`; audited current-model fallback after three raw failures |
| Focused debugging | `debugger` | prefer `gpt-5.6-terra`; audited current-model fallback after three raw failures |
| Deterministic test/build/checklist execution | `luna_verifier` | prefer `gpt-5.6-luna`; otherwise `luna_route_fallback` |
| Browser, lifecycle, external-effect, and stage journey acceptance | `terra_acceptance` using Ego Lite `ego-browser` for every browser operation | prefer `gpt-5.6-terra`; otherwise audited fallback after three raw failures |
| Final exact-target acceptance | `terra_final_acceptance` | prefer `gpt-5.6-terra`; otherwise fresh independent audited fallback reviewer |
| Plan/architecture/security escalation | planning reviewer | prefer `gpt-5.6-sol`; otherwise current model under `sol_route_fallback` |

Model identity is a runtime contract. Pass the explicit preferred model when the surface supports it
and verify observed metadata; a role name is not evidence. Raw native spawn arguments plus child
runtime model are authoritative, while route-guard nonce evidence is optional.

All browser acceptance uses the exclusive Ego Lite contract in [browser-acceptance-contract.md](browser-acceptance-contract.md); the model decides the verdict, while `ego-browser` owns the browser interaction and evidence capture.

Every new model context starts with a no-write routing handshake. Do not send repository-write
authority or the execution packet until runtime metadata proves the requested model. A mismatch
invalidates the delegated turn and quarantines its output as diagnostic only. For
implementation-class work, discard the failed context and let the current main agent continue with
its existing model under `terra_route_fallback` only after three sequential handshake attempts
have failed.

## Program budget

Count every spawned child Agent cumulatively across all Goal sessions: target 8, soft limit 12, hard limit 20. Limit nesting to one level and active Goal sessions to three. Completed or failed Agents still count toward the cumulative total. Only the program controller may allocate new budget.

## Executor autonomy

Executors may reuse an equivalent helper/type, adjust local placement, reorder steps within one task, change test mechanics, and make reversible internal changes that preserve contracts. Record material deviations.

Executors may not silently change approved architecture, public contracts, product behavior, safety, data ownership, task scope, persistence, runtime ownership, or acceptance.

## Escalation packet

Plan conflicts must include:

```yaml
escalation_id:
affected_task:
plan_version:
failed_assumption_or_decision:
observed_evidence: []
impact_on_current_task:
impact_on_downstream_tasks: []
options_considered: []
reversible_changes_already_made: []
recommended_review:
```

## Revision invalidation

When a planning revision changes a consumed contract, mark affected pending and completed-but-unverified attempts `stale`, record the new plan revision, and rerun only the evidence invalidated by the change. Sol fallback changes only the model route, not the invalidation rules. Do not erase prior evidence.

## Retry policy

Retry only after identifying a changed hypothesis, input, implementation, or environment. Repeating the same failing attempt is not progress. Escalate after the plan's threshold or when the failure crosses an authority boundary.

## Parallelism

Parallelize only when dependencies are satisfied, contracts are stable, worktrees/write scopes do not overlap, development ports are isolated, and integration ordering is explicit. The program controller integrates results; executors do not negotiate shared contracts independently.
