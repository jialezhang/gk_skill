---
name: assess-goal-scope
description: Use after an approved PRD and before implementation planning when delivery size, parallelization, or Goal boundaries are uncertain.
---

# Assess Goal Scope

The current main agent prefers `gpt-5.6-sol` for this skill. Verify the current runtime turn before
assessment work. An Agent name, role, or prompt is not model evidence. If Sol is not listed,
selection is rejected, or the observed route mismatches, continue with the current model and append
an evidenced `sol_route_fallback` record. Never return `MAIN_AGENT_SOL_REQUIRED` or block Goal
packaging solely because Sol is unavailable.

Estimate delivery size from repository evidence before committing to one Goal. Keep cumulative Agent workload, Program wall-clock critical path, and external wait as separate quantities. P80 is the wall-clock duration that the assessment expects not to exceed in 80% of comparable executions; it is a calibrated range, not a promise.

Read [references/sizing-contract.md](references/sizing-contract.md) completely.

## Assess

1. Inspect the approved PRD, actual repository entry points, tests, ownership boundaries, runtime/deployment requirements, and concurrent work. Do not estimate from PRD length.
2. Measure current repository automation where safe: focused/full check duration, build/startup, sandbox setup, evidence generation, and recent completion receipts. Prefer those measurements over generic manual-development estimates.
3. Classify readiness as `verified_materialized`, `partially_materialized`, `not_materialized`, or `unknown`. Do not charge verified materialized work again. Put known missing work in the base scenario; model partial or unknown readiness as mutually exclusive conditional branches.
4. Split the remaining work into independently verifiable packages. For each package record optimistic, P50, P80, and conservative active workload plus evidence and uncertainty.
5. Record product/test files likely to change, domains crossed, dependency and write-conflict graphs, exact-target environments, protected-data risk, external wait, and integration work.
6. Assign common-cause risks to correlation groups before computing percentiles. Do not sum overlapping task, retry, integration, and Program buffers.
7. Compute cumulative Agent workload separately from sequential and parallel wall-clock paths. In schema 1.1, `p50_hours == critical_path_p50_hours` and `p80_hours == critical_path_p80_hours`; the path includes integration, clean-commit verification, and only non-duplicated retry/environment allowance.
8. When readiness is partial or unknown, define `G-00` as the mandatory evidence gate that selects the branch and re-estimates remaining work before implementation proceeds.
9. Create `scope-assessment.yaml` from [assets/scope-assessment-template.yaml](assets/scope-assessment-template.yaml).

## Decide Goal boundaries

- P80 at most 5 hours: normally one Goal.
- P80 above 5 and at most 8 hours: one Goal is acceptable with checkpoint commits.
- P80 above 8 hours: set `split_recommended: true` and ask whether to split.
- P80 above 10 hours: set `split_strength: strong`.
- More than 50 expected files, four or more domains, or combined authorization/data/background-runtime risk also triggers a split discussion even if the time estimate is lower.
- Prefer 2–3 independently deliverable Goals. More than 3 usually requires a program-level product split.

When a split is recommended, present the proposed Goals, dependency/conflict graph, estimated critical path, worktrees/sessions, integration owner, and recommendation. Ask the user to choose split or single Goal. If the user-input mechanism supports auto-resolution, use a 240-second timeout. No response resolves to:

```yaml
split_decision: single_goal
decision_source: timeout_default_single
decision_timeout_seconds: 240
```

Silence is never approval of a PRD or plan; this timeout applies only to Goal packaging.

## Validate and hand off

Run (schema 1.0 remains readable; new assessments use schema 1.1):

```bash
python3 scripts/validate_scope_assessment.py <scope-assessment.yaml>
```

Hand the validated assessment and explicit/default decision to `$create-implementation-plan`. Do not implement product code in this stage.
