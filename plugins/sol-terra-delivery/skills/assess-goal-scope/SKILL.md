---
name: assess-goal-scope
description: Use after an approved PRD and before implementation planning when delivery size, parallelization, or Goal boundaries are uncertain.
---

# Assess Goal Scope

Estimate delivery size from repository evidence before committing to one Goal. P80 is the wall-clock duration that the assessment expects not to exceed in 80% of comparable executions; it is a calibrated range, not a promise.

Read [references/sizing-contract.md](references/sizing-contract.md) completely.

## Assess

1. Inspect the approved PRD, actual repository entry points, tests, ownership boundaries, runtime/deployment requirements, and concurrent work. Do not estimate from PRD length.
2. Split the work into independently verifiable packages. For each package record optimistic, P50, P80, and conservative duration plus evidence and uncertainty.
3. Record product/test files likely to change, domains crossed, dependency and write-conflict graphs, exact-target environments, protected-data risk, and integration work.
4. Estimate sequential and parallel wall-clock paths. `critical_path_p80_hours` includes integration, clean-commit verification, and realistic retry/environment allowance.
5. Create `scope-assessment.yaml` from [assets/scope-assessment-template.yaml](assets/scope-assessment-template.yaml).

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

Run:

```bash
python3 scripts/validate_scope_assessment.py <scope-assessment.yaml>
```

Hand the validated assessment and explicit/default decision to `$create-implementation-plan`. Do not implement product code in this stage.
