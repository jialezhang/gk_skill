---
tasks_status: PLAN_REVIEW_REQUIRED
plan_version: 1.0.0
---

# Tasks: Status indicator

## Task Index

| ID | Milestone | Outcome | Dependencies | Role | Gate | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | M1 | Show running state | none | frontend_executor | G-001 | pending |

## [T-001] Show the authoritative running state

- **Requirements:** R-001
- **Dependencies:** none
- **Contracts consumed:** DEC-001
- **Commitments:** DEC-001
- **Preferred role:** frontend_executor
- **Write scope:** status component and focused test
- **Outcome:** running work is visible
- **Acceptance:** J-001 is observable
- **Verification:**
  - test_level: change
  - risk and impact surface: status projection and production route
  - focused/change commands: focused render test and SC-001
  - full-run reason: not_applicable
  - Provider mode: not_applicable
  - Provider budget/call limit: not_applicable
  - evidence invalidation keys: commit, build, route
  - 阶段真实用户旅程/ exact-target handoff: SC-001
- **Rollback/disable:** revert bounded component change
- **Escalate to Sol when:** a second state owner is required
- **Evidence destination:** evidence/T-001

## Gates

### [G-001] Real running state

- Prerequisites: T-001
- Exact target: production route with real running task
- Required evidence: AC-001
- Pass condition: status is visible
- Failure routing: local rework or plan conflict
- Downstream tasks blocked on failure: completion
