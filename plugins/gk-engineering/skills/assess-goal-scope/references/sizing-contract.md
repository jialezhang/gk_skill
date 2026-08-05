# Sizing Contract

## Required estimate identities

`p50_hours`, `p80_hours`, and `p90_hours` are Program wall-clock percentiles. In schema 1.1 they describe the same dependency path as `critical_path_p50_hours` and `critical_path_p80_hours`, so the matching fields must be equal. P80 means that 80% of genuinely comparable deliveries should finish within that wall-clock duration; it is not a promise and is never the sum of every package's P80.

Track `cumulative_workload_p50_hours` and `cumulative_workload_p80_hours` separately. These are the sum of active Agent execution across all parallel lanes and must not be reported as completion time. Track expected queue, provider, approval, or environment wait separately as `expected_wait_*`; include only the portion that actually lies on the critical path in the wall-clock estimate.

## Evidence basis

Build estimates from work packages and repository inspection. Each package records:

- observable outcome and exact-target proof;
- optimistic, P50, P80, and conservative duration;
- likely files and system domains;
- dependencies and write conflicts;
- environment, migration, authorization, data, or lifecycle uncertainty;
- integration and retry allowance.

Prefer evidence in this order:

1. measured durations from the current repository's commands, harnesses, and recent delivery receipts;
2. comparable historical actuals from the same delivery system;
3. measured component durations plus calibrated ranges;
4. explicit ranges with no history.

Agentic automation changes the baseline. Do not import human/manual calendar estimates for code generation, deterministic checks, repository search, or evidence assembly when the current automation can be measured. Conversely, do not omit real external waits, exact-target startup, provider latency, deployment, protected-data handling, or browser journeys when they are in scope. False precision is a finding: do not claim decimal-hour confidence without calibrated data.

## Readiness scenarios and re-estimation

Classify readiness as `verified_materialized`, `partially_materialized`, `not_materialized`, or `unknown` using repository evidence.

- Verified materialized work is excluded from the remaining baseline.
- Known missing work belongs in the base work packages; it is not a probabilistic tail.
- Partial or unknown readiness requires explicit `conditional_estimates`, estimate invalidation keys, and a `G-00` re-estimation gate.

Do not blend mutually exclusive readiness outcomes into one inflated base estimate. Record a base scenario and conditional wall/workload adders with their trigger evidence. At G-00, resolve the branch, replace the provisional estimate with a new revision, and re-estimate the remaining—not elapsed—work. Preserve the prior revision for audit. If the new wall-clock P80 crosses a split threshold or invalidates Goal packaging, return the packaging decision to the user; otherwise update the estimate without reopening approved product scope.

## Tail-risk correlation

Give risks caused by the same underlying uncertainty one `risk_correlation_group`. Charge a common-cause allowance once on the path where it can occur. Do not add package P80s, retry allowances, integration buffers, and a Program contingency when they cover the same failure. Mutually exclusive branches are alternatives, not cumulative adders. A Program P80 is the percentile of scenario-specific critical paths after dependency and correlation analysis.

Keep tests as work packages only to the extent that their measured execution, diagnosis, and repair time is on the remaining path. Repeated runs of unchanged checks are not independent risk events.

## Split quality

A proposed Goal must have an independently reviewable outcome, bounded write scope, focused verification, worktree/branch, session owner, and checkpoint commit. Splits that merely separate frontend from backend while sharing unstable contracts are unsafe.

The scope assessment recommends packaging; the implementation plan owns the final task DAG inside the selected Goal structure.
