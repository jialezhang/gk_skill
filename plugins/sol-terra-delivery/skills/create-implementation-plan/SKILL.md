---
name: create-implementation-plan
description: Create or revise a complete evidence-based implementation baseline from an explicitly approved PRD. Use for medium, large, cross-module, migration, agent-runtime, asynchronous or event-driven, data, or high-risk features that need readiness analysis, a full task DAG, delegation guidance, lifecycle and state-convergence contracts, gates, rollback, and exact-target verification before Goal-driven delivery.
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

Require `prd_status: APPROVED`. If the PRD is not approved, return `PRD_APPROVAL_REQUIRED` without planning around the gate.

## Procedure

### Phase 1: Direction readiness

1. Read the PRD, constitution, repository rules, current code, tests, architecture decisions, incidents, and relevant official dependency documentation.
2. Freeze exact target identity and current responsibility owners, including the authoritative owner of every long-running operation and user-visible status.
3. Classify every requested change as `local fix`, `compatible extension`, or `incompatible constraint` using direct evidence.
4. Challenge rewrites, new runtimes, new persistence, and new domain objects. Require an explicit incompatibility or approved organizational constraint.
5. For asynchronous or event-driven journeys, trace interaction, command, business-work, persistence, projection, and reconnect lifecycles separately. Never infer that an interaction or transport terminal state ends the underlying business work.
6. Convert discoverable uncertainty into `VERIFY_FIRST` tasks. Return `READINESS_BLOCKED` only when progress requires missing authority, unavailable evidence, or a product decision.

### Phase 2: Architecture baseline

1. Build responsibility-replacement, field-level data/identity/safety flow, compatibility, migration, rollback, and Legacy maps.
2. For asynchronous or event-driven journeys, define the runtime lifecycle and state-convergence contract: distinct lifecycle identities, terminal-state ownership, correlation keys, subscription lifetime, authoritative snapshot, reconnect/event-loss recovery, ordering/idempotency, convergence bound, and duplicate-side-effect prevention.
3. Define the earliest real vertical slice and falsifiers that stop unjustified expansion. The slice must include interruption and recovery when lifecycle continuity is part of the risk.
4. Record alternatives and why they were rejected.
5. Mark every decision `MUST`, `BASELINE`, `VERIFY_FIRST`, `RECOMMENDED`, `DEFERRED`, or `FORBIDDEN`.
6. Create the complete project baseline using [assets/implementation-plan-template.md](assets/implementation-plan-template.md).

### Phase 3: Complete task decomposition

1. Map every approved requirement and acceptance journey to task and evidence IDs before drafting prose tasks.
2. Create a dependency-ordered DAG using [assets/tasks-template.md](assets/tasks-template.md). Plan the entire approved scope, not only the first milestone.
3. Define role, required skills, bounded write scope, consumed contracts, parallel safety, verification, rollback, evidence destination, and escalation triggers for every task.
4. Put high-risk assumptions and the first real slice before broad infrastructure or speculative abstraction.
5. Keep exact files/APIs for distant work non-binding unless already verified.

### Phase 4: Verification design

1. Create `verification.md` from [assets/verification-template.md](assets/verification-template.md).
2. Define focused, integration, regression, and exact-target cases for every blocking journey.
3. For every applicable long-running journey, require exact-target cases for normal completion, reconnect during work, dropped/delayed/duplicate terminal events, failure/cancellation, retry supersession, cross-surface agreement, and bounded convergence from the authoritative snapshot.
4. Define gate prerequisites, evidence, forbidden substitutions, stop action, and recovery owner.
5. Distinguish `Implemented`, `Enabled`, `Executed`, `Verified`, and `Complete`.

### Phase 5: Independent review

1. Spawn a fresh Sol-class reviewer that did not author the plan. Give it approved product artifacts, plan artifacts, repository evidence, and decision records.
2. Run requirement coverage, dependency, ownership, lifecycle/state-convergence, safety, rollback, false-precision, delegation, and exact-target reviews.
3. Return each finding to its owning artifact; do not patch PRD gaps inside tasks.
4. Run `python3 scripts/validate_plan_artifacts.py --prd <spec.md> --plan <plan.md> --tasks <tasks.md> --verification <verification.md>` from this skill directory.
5. Resolve all blocking/major plan-owned findings, then set `plan_status` and `tasks_status` to `PLAN_REVIEW_REQUIRED`. Never approve them yourself.

## Output discipline

- Be highly specific when evidence supports specificity: contracts, ownership, IDs, dependencies, invariants, commands, and verified touchpoints.
- Mark unverified APIs, event shapes, file paths, abstractions, and distant task mechanics as provisional instead of presenting them as facts.
- Avoid repeating global constraints inside every task; reference stable IDs.
- Preserve a complete baseline for cross-model continuity while loading only the current execution packet during delivery.
- Record output paths, revisions, evidence gaps, review verdict, and the exact approval boundary in the final handoff.
