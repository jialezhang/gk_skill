---
name: create-implementation-plan
description: Use when an approved PRD and validated scope decision need an evidence-based technical baseline before implementation begins.
---

# Create Implementation Plan

The current main agent is the sole implementation-plan author and reviewer. Prefer `gpt-5.6-sol`; if it is not listed, selection is rejected, or the observed route mismatches, continue with the current model and record `sol_route_fallback` with live evidence. Do not return `MAIN_AGENT_SOL_REQUIRED` or block the Goal. Do not spawn, create, or delegate to a child agent, subagent, separate reviewer context, or separate task for planning, review, revision, or validation. Do not implement product code in this stage.

Read all references completely:

- [references/readiness-protocol.md](references/readiness-protocol.md)
- [references/planning-contract.md](references/planning-contract.md)
- [references/task-decomposition.md](references/task-decomposition.md)
- [references/verification-contract.md](references/verification-contract.md)
- [references/test-strategy-contract.md](references/test-strategy-contract.md)
- [references/plan-review.md](references/plan-review.md)

## Preconditions

Require `prd_status: APPROVED` and a validated `scope-assessment.yaml` whose split decision is not pending. If the PRD is not approved, return `PRD_APPROVAL_REQUIRED`. If scope is missing or pending, return `SCOPE_DECISION_REQUIRED`.

## Procedure

### Phase 1: Direction readiness

1. Read the PRD, constitution, repository rules, current code, tests, architecture decisions, incidents, and relevant official dependency documentation.
2. Reconcile the scope assessment against repository evidence. Preserve every prior estimate revision and explain changes. Do not silently lower P80 or remove a split recommendation; do lower or raise the new estimate when measured evidence, corrected path math, readiness, or risk-correlation analysis requires it.
3. Freeze exact target identity and current responsibility owners, including the authoritative owner of every long-running operation and user-visible status.
4. Classify every requested change as `local fix`, `compatible extension`, or `incompatible constraint` using direct evidence.
5. Challenge rewrites, new runtimes, new persistence, and new domain objects. Require an explicit incompatibility or approved organizational constraint.
6. For asynchronous or event-driven journeys, trace interaction, command, business-work, persistence, projection, and reconnect lifecycles separately. Never infer that an interaction or transport terminal state ends the underlying business work.
7. Convert discoverable uncertainty into `VERIFY_FIRST` tasks. For partial or unknown readiness, make `G-00` select the conditional branch and re-estimate remaining cumulative workload and critical-path wall-clock time. Return `READINESS_BLOCKED` only when progress requires missing authority, unavailable evidence, or a product decision.

### Phase 2: Architecture baseline

1. Build responsibility-replacement, field-level data/identity/safety flow, compatibility, migration, rollback, and Legacy maps.
2. For asynchronous or event-driven journeys, define the runtime lifecycle and state-convergence contract: distinct lifecycle identities, terminal-state ownership, correlation keys, subscription lifetime, authoritative snapshot, reconnect/event-loss recovery, ordering/idempotency, convergence bound, and duplicate-side-effect prevention.
3. Define the earliest 阶段真实用户旅程 and falsifiers that stop unjustified expansion. The journey must include interruption and recovery when lifecycle continuity is part of the risk. Every browser journey must specify Ego Lite `ego-browser` as the exclusive interaction and evidence runner.
4. Record alternatives and why they were rejected.
5. Mark every decision `MUST`, `BASELINE`, `VERIFY_FIRST`, `RECOMMENDED`, `DEFERRED`, or `FORBIDDEN`.
6. Create the complete project baseline using [assets/implementation-plan-template.md](assets/implementation-plan-template.md).

### Phase 2A: Goal packaging and environments

1. For `single_goal`, create one Goal plan and record that the user explicitly selected or timed out to `timeout_default_single` when P80 exceeded 8 hours.
2. For `split`, create one program baseline plus 2–3 Goal plans. Each Goal needs an independently reviewable outcome, active-workload and wall-clock P50/P80 ranges, bounded write scope, visible session, worktree, branch, development port/browser context, checkpoint, and exact-target handoff.
3. Add cross-Goal dependency and write-conflict graphs. Parallelize only independent waves; maximum parallel Goal sessions is 3.
4. Assign one Terra integration owner and a clean integration worktree. Do not make every Goal its own program controller.
5. Define the cumulative Agent budget: target 8, soft limit 12, hard limit 20 across the whole program. Agent count is a concurrency constraint, not a multiplier for wall-clock duration.

### Phase 3: Complete task decomposition

1. Map every approved requirement and acceptance journey to task and evidence IDs before drafting prose tasks.
2. Create a dependency-ordered DAG using [assets/tasks-template.md](assets/tasks-template.md). Plan the entire approved scope, not only the first milestone.
3. Define Goal, role, required skills, bounded write scope, consumed contracts, parallel safety, active-workload and wall-clock ranges, estimate evidence, conditional/risk group, verification, rollback, checkpoint, evidence destination, and escalation triggers for every task.
4. Put high-risk assumptions and the first 阶段真实用户旅程 before broad infrastructure or speculative abstraction.
5. Give every task a risk-driven `test_level` (`fast`, `change`, or `full`), impact surface, invalidation keys, external-effect policy/IDs, and explicit full-run reason when applicable.
5. Keep exact files/APIs for distant work non-binding unless already verified.

### Phase 4: Verification design

1. Create `verification.md` from [assets/verification-template.md](assets/verification-template.md).
2. Separate acceptance claims (`AC-*`) from execution scenarios (`SC-*`). Let one scenario prove multiple claims when it uses the same path.
3. For every applicable long-running journey, require exact-target cases for normal completion, reconnect during work, dropped/delayed/duplicate terminal events, failure/cancellation, retry supersession, cross-surface agreement, and bounded convergence from the authoritative snapshot. Browser cases must follow the Ego Lite `ego-browser` contract.
4. Define `fast`, `change`, and `full` suites, with full regression/build reserved for a frozen candidate or a documented risk trigger.
5. Define project-profile external-effect policies, authorization and limits. Do not expand an unjustified Cartesian matrix; require explicit interaction-risk evidence and execution budget when one is necessary.
6. Define candidate identity, evidence reuse/invalidation rules, gate prerequisites, forbidden substitutions, stop action, and recovery owner.
7. Distinguish `Implemented`, `Enabled`, `Executed`, `Verified`, and `Complete`.

### Phase 5: Main-agent review

1. The current main agent starts a distinct review pass by rereading the PRD, scope decision, repository evidence, and all planning artifacts without opening another agent or task.
2. Run the structural/coverage checklist and assess repository feasibility, worktree/write-conflict risk, execution practicality, and verification practicality directly.
3. Resolve architecture choices, high-risk security boundaries, and product-plan contradictions in the owning artifact; return product-owned decisions to the user.
4. Run requirement coverage, dependency, ownership, lifecycle/state-convergence, safety, rollback, false-precision, delegation, Goal sizing, checkpoint, and exact-target reviews.
5. Return each finding to its owning artifact; do not patch PRD gaps inside tasks.
6. Run `python3 scripts/validate_plan_artifacts.py --prd <spec.md> --plan <plan.md> --tasks <tasks.md> --verification <verification.md>` from this skill directory.
7. Resolve all blocking/major plan-owned findings, then set `plan_status` and `tasks_status` to `PLAN_REVIEW_REQUIRED`. Never approve them yourself.

## Output discipline

- Be highly specific when evidence supports specificity: contracts, ownership, IDs, dependencies, invariants, commands, and verified touchpoints.
- Mark unverified APIs, event shapes, file paths, abstractions, and distant task mechanics as provisional instead of presenting them as facts.
- Avoid repeating global constraints inside every task; reference stable IDs.
- Preserve a complete baseline for cross-model continuity while loading only the current execution packet during delivery.
- Record output paths, revisions, evidence gaps, review verdict, and the exact approval boundary in the final handoff.
- Implementation-plan ownership remains with the current main agent through every revision, including changes requested during delivery or gate review.
