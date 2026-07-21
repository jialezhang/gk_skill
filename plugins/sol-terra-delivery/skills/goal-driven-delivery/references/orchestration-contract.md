# Orchestration Contract

## Single runtime owner

The Terra delivery controller is the only owner of live execution state. Spec Kit artifacts are durable baselines, not a second scheduler. Sol reviewers may revise plans and issue verdicts but do not dispatch implementation while Terra is active.

## Role routing

| Work | Default role | Default model/effort |
| --- | --- | --- |
| Runtime scheduling and integration | `terra_delivery` | `gpt-5.6-terra` / high |
| Frontend implementation | `frontend_executor` | `gpt-5.6-terra` / high |
| Backend implementation | `backend_executor` | `gpt-5.6-terra` / high |
| Data/migration implementation | `data_executor` | `gpt-5.6-terra` / high |
| Focused debugging | `debugger` | configured standard model / high |
| Test design and verification | `test_executor` / `verifier` | Terra or configured verifier |
| Plan revision and gate review | `sol_planner` / `sol_reviewer` | `gpt-5.6-sol` / xhigh |

Treat names as roles; model mapping is configurable. Preserve the authority boundary even when models change.

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

When Sol changes a consumed contract, mark affected pending and completed-but-unverified attempts `stale`, record the new plan revision, and rerun only the evidence invalidated by the change. Do not erase prior evidence.

## Retry policy

Retry only after identifying a changed hypothesis, input, implementation, or environment. Repeating the same failing attempt is not progress. Escalate after the plan's threshold or when the failure crosses an authority boundary.

## Parallelism

Parallelize only when dependencies are satisfied, contracts are stable, write scopes do not overlap, and integration ordering is explicit. The controller integrates results; executors do not negotiate shared contracts independently.
