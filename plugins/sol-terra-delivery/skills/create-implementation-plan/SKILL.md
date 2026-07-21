---
name: create-implementation-plan
description: Use when an approved PRD and validated scope decision need an evidence-based technical baseline before implementation begins.
---

# Create Implementation Plan

Use a Sol-class planning agent for this stage. Do not implement product code.

Read all references completely:

- [references/readiness-protocol.md](references/readiness-protocol.md)
- [references/planning-contract.md](references/planning-contract.md)
- [references/task-decomposition.md](references/task-decomposition.md)
- [references/verification-contract.md](references/verification-contract.md)
- [references/plan-review.md](references/plan-review.md)

## Preconditions

Require `prd_status: APPROVED` and a validated `scope-assessment.yaml` whose split decision is not pending. If the PRD is not approved, return `PRD_APPROVAL_REQUIRED`. If scope is missing or pending, return `SCOPE_DECISION_REQUIRED`.

## Procedure

### Phase 1: Direction readiness

1. Read the PRD, constitution, repository rules, current code, tests, architecture decisions, incidents, and relevant official dependency documentation.
2. Reconcile the scope assessment against repository evidence. Do not silently lower P80 or remove a split recommendation to simplify planning.
3. Freeze exact target identity and current responsibility owners, including the authoritative owner of every long-running operation and user-visible status.
4. Classify every requested change as `local fix`, `compatible extension`, or `incompatible constraint` using direct evidence.
5. Challenge rewrites, new runtimes, new persistence, and new domain objects. Require an explicit incompatibility or approved organizational constraint.
6. For asynchronous or event-driven journeys, trace interaction, command, business-work, persistence, projection, and reconnect lifecycles separately. Never infer that an interaction or transport terminal state ends the underlying business work.
7. Convert discoverable uncertainty into `VERIFY_FIRST` tasks. Return `READINESS_BLOCKED` only when progress requires missing authority, unavailable evidence, or a product decision.

### Phase 2: Architecture baseline

1. Build responsibility-replacement, field-level data/identity/safety flow, compatibility, migration, rollback, and Legacy maps.
2. For asynchronous or event-driven journeys, define the runtime lifecycle and state-convergence contract: distinct lifecycle identities, terminal-state ownership, correlation keys, subscription lifetime, authoritative snapshot, reconnect/event-loss recovery, ordering/idempotency, convergence bound, and duplicate-side-effect prevention.
3. Define the earliest real vertical slice and falsifiers that stop unjustified expansion. The slice must include interruption and recovery when lifecycle continuity is part of the risk.
4. Record alternatives and why they were rejected.
5. Mark every decision `MUST`, `BASELINE`, `VERIFY_FIRST`, `RECOMMENDED`, `DEFERRED`, or `FORBIDDEN`.
6. Create the complete project baseline using [assets/implementation-plan-template.md](assets/implementation-plan-template.md).

### Phase 2A: Goal packaging and environments

1. For `single_goal`, create one Goal plan and record that the user explicitly selected or timed out to `timeout_default_single` when P80 exceeded 8 hours.
2. For `split`, create one program baseline plus 2–3 Goal plans. Each Goal needs an independently reviewable outcome, P50/P80 range, bounded write scope, visible session, worktree, branch, development port/browser context, checkpoint, and exact-target handoff.
3. Add cross-Goal dependency and write-conflict graphs. Parallelize only independent waves; maximum parallel Goal sessions is 3.
4. Assign one Terra integration owner and a clean integration worktree. Do not make every Goal its own program controller.
5. Define the cumulative Agent budget: target 8, soft limit 12, hard limit 20 across the whole program.

### Phase 3: Complete task decomposition

1. Map every approved requirement and acceptance journey to task and evidence IDs before drafting prose tasks.
2. Create a dependency-ordered DAG using [assets/tasks-template.md](assets/tasks-template.md). Plan the entire approved scope, not only the first milestone.
3. Define Goal, role, required skills, bounded write scope, consumed contracts, parallel safety, verification, rollback, checkpoint, evidence destination, and escalation triggers for every task.
4. Put high-risk assumptions and the first real slice before broad infrastructure or speculative abstraction.
5. Keep exact files/APIs for distant work non-binding unless already verified.

### Phase 4: Verification design

1. Create `verification.md` from [assets/verification-template.md](assets/verification-template.md).
2. Define focused, integration, regression, and exact-target cases for every blocking journey.
3. For every applicable long-running journey, require exact-target cases for normal completion, reconnect during work, dropped/delayed/duplicate terminal events, failure/cancellation, retry supersession, cross-surface agreement, and bounded convergence from the authoritative snapshot.
4. Define gate prerequisites, evidence, forbidden substitutions, stop action, and recovery owner.
5. Distinguish `Implemented`, `Enabled`, `Executed`, `Verified`, and `Complete`.

### Phase 5: Independent review

1. Run deterministic validation and use `gpt-5.6-luna` for the structural/coverage checklist.
2. Use a fresh Terra context for repository feasibility, worktree/write-conflict, execution, and verification practicality review.
3. Spawn a second Sol reviewer only when the plan contains an unresolved architecture choice, high-risk security boundary, product-plan contradiction, or explicit user request. Do not spend Sol on a routine checklist.
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
