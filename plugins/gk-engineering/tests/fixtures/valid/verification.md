---
verification_status: PLAN_REVIEW_REQUIRED
plan_version: 1.0.0
---

# Verification: Status indicator

## Target Identity
Production route and real running task.

## Automated and Integration Matrix

| Requirement/task | Check | Evidence |
| --- | --- | --- |
| R-001 / T-001 | focused render test | evidence/T-001 |

## Runtime Lifecycle and Convergence Matrix
Verify the production route reconciles the authoritative running state after reconnect and does not repeat side effects.

## Exact-target Acceptance Cases

### AC-001: Observe real running state

- Exact target: production route
- Observable result: running status is visible
- Forbidden substitutions: fixture-only route
- Failure routing: T-001

## Execution Scenario Coverage

### SC-001: Observe one real running task

- Proves: AC-001
- Stage: 阶段真实用户旅程
- Exact target: production route
- External effect policy: not_applicable
- External effect IDs: not_applicable
- External effect authorization/budget: not_applicable
- Actions: open the task and observe status
- Evidence paths: evidence/T-001
- Invalidation keys: commit, build, route
- Matrix type: representative
- Interaction risk: not_applicable
- Pairwise insufficient because: not_applicable
- Estimated executions: 1
- Budget: not_applicable

## Candidate Evidence Policy

- Candidate commit/build: frozen before full verification
- Full-suite trigger: candidate freeze
- Same-candidate evidence index: evidence/index.json
- Evidence reuse rule: reuse until invalidation key changes
- Invalidation keys: commit, build, route
- Independent Terra final-acceptance thread: required

## Gate Matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| G-001 | AC-001 | pending |

## Final Reconciliation
Pending G-001.
