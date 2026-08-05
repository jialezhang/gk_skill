---
verification_status: PLAN_REVIEW_REQUIRED
plan_version: 0.1.0
---

# Verification: [Feature]

## Target Identity

- Product/module:
- Entry/route:
- Build/commit:
- Clean worktree:
- Model-routing log/Canary:
- Flags/configuration:
- User/owner:
- Data:
- External effects:

## Automated and Integration Matrix

| Requirement/task | Test level | Check | Command/operation | Invalidation keys | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |

## Runtime Lifecycle and Convergence Matrix

- Applicability: applicable | not applicable, with evidence
- Authoritative status source:
- Declared convergence bound:

| Journey | Lifecycle/correlation | Interruption or event condition | Expected authoritative result | Surfaces that must converge | Duplicate-side-effect check | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Exact-target Acceptance Cases

### AC-001: [Blocking journey]

- Preconditions:
- Exact target:
- Browser runner when applicable: Ego Lite `ego-browser` exclusively
- Ego Lite task-space, URL, screenshots/snapshots, and `completeTaskSpace` cleanup evidence:
- User/owner:
- External effects/data:
- Actions:
- Observable result:
- Authoritative persisted result:
- Interruption/reconnect and event-loss conditions when applicable:
- Cross-surface convergence deadline when applicable:
- Duplicate-side-effect protection when applicable:
- Evidence paths:
- Forbidden substitutions:
- Failure routing:

## Execution Scenario Coverage

### SC-001: [One executable journey]

- Proves: AC-001
- Stage: [阶段真实用户旅程 | final]
- Exact target:
- External effect policy: forbidden | sandboxed | authorized | not_applicable
- External effect IDs: not_applicable | [IDs from project-profile.json]
- External effect authorization/budget: not_applicable | [authorization reference, budget, and limits]
- Actions:
- Evidence paths:
- Invalidation keys:
- Matrix type: representative | pairwise | cartesian
- Interaction risk: not_applicable | [risk]
- Pairwise insufficient because: not_applicable | [reason]
- Estimated executions: 1
- Budget: not_applicable | [time/cost]

## Candidate Evidence Policy

- Candidate commit/build:
- Full-suite trigger:
- Same-candidate evidence index:
- Evidence reuse rule:
- Invalidation keys:
- Independent Terra or audited Terra-fallback final-acceptance thread:

## Gate Matrix

| Gate | Prerequisites | Required evidence | Pass condition | Failure action | Status |
| --- | --- | --- | --- | --- | --- |

## Final Reconciliation

- Implemented:
- Enabled:
- Executed:
- Verified:
- Complete:
- Remaining non-blocking risks:
- Checkpoint commits pushed/reported:
- Integrated clean commit (multi-Goal):
