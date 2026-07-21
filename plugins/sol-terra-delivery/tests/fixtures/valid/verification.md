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

## Gate Matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| G-001 | AC-001 | pending |

## Final Reconciliation
Pending G-001.
