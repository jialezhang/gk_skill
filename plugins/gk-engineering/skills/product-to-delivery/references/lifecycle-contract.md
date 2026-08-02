# Lifecycle Contract

## Program state machine

```text
ROUTING_DECISION_PENDING
├─ PRD_NOT_REQUIRED
│  → TECHNICAL_CHANGE_ACTIVE
│  → TECHNICAL_CHANGE_VERIFIED
└─ PRD_REQUIRED
   → DISCOVERY_IN_PROGRESS
   → DISCOVERY_READY
   → PRD_DRAFT
   → REVIEW_REQUIRED
   → APPROVED
   → SCOPE_ASSESSMENT
   → GOAL_BOUNDARIES_DECIDED
   → PLAN_DRAFT
   → PLAN_REVIEW_REQUIRED
   → PLAN_APPROVED
   → DELIVERY_ACTIVE
   → GATE_REVIEW
   → TARGET_VERIFIED
   → COMPLETE
```

For a multi-Goal delivery, keep one runtime Program Goal active for the full lifecycle. Goal sessions are milestones:

```text
PROGRAM_ACTIVE
→ Goal 1 GOAL_TARGET_VERIFIED
→ Goal 2 GOAL_TARGET_VERIFIED
→ Goal 3 GOAL_TARGET_VERIFIED
→ PROGRAM_INTEGRATION_PENDING
→ PROGRAM_TARGET_VERIFIED
→ COMPLETE
```

Never map a milestone checkpoint or `GOAL_TARGET_VERIFIED` to Program completion. Persist the Program in `program-state.yaml`, initialized from `assets/program-state-template.yaml`, and validate it before any completion transition:

```bash
python3 scripts/validate_program_state.py <program-state.yaml>
```

## Legacy-state recovery

When resuming a delivery created before Program state existed:

1. reconstruct approved scope, child Goal states, commits, gates, and remaining release work;
2. initialize Program state without erasing or relabelling historical evidence;
3. map a formerly completed child Goal to `GOAL_TARGET_VERIFIED`, not Program completion;
4. if the old runtime Goal was already completed while required work remains, create one replacement runtime Program Goal and record the former ID/reason in `superseded_runtime_goals`;
5. recompute the four fixed denominators from the approved plan and durable evidence;
6. validate Program and candidate state before continuing.

Do not reset progress, create a fresh delivery history, or claim the old Goal completion proved integration/final acceptance.

`completion_scope` is explicit: `branch`, `merged`, `deployed`, or `production_verified`. Report later release states independently rather than calling a branch-verification result deployed.

Exceptional states:

- `DISCOVERY_BLOCKED`: a material product choice is missing.
- `READINESS_BLOCKED`: implementation direction lacks decisive repository or runtime evidence.
- `PLAN_CONFLICT`: execution evidence contradicts the approved baseline.
- `PRODUCT_DECISION_REQUIRED`: resolving a conflict changes the approved PRD.
- `VERIFICATION_BLOCKED`: the exact target cannot be exercised.

## Required artifacts

Use the active Spec Kit feature directory when present. Otherwise use the repository's established docs convention.

| Stage | Durable artifact |
| --- | --- |
| Discovery | completed conversation and optional `discovery.md` |
| Product | `spec.md` with approval metadata |
| Scope | `scope-assessment.yaml` with P50/P80/P90 and split decision |
| Planning | program/Goal `plan.md`, `tasks.md`, `verification.md` |
| Delivery | one `program-state.yaml`; per-Goal `delivery-state.yaml`, `model-routing.jsonl`, baseline/impact/evidence index, candidate manifest, exact-turn telemetry, decision log |
| Integration | integration commit, merge/evidence index, program status |

## Handoffs

- Discovery → PRD: confirmed product decisions, unresolved product questions, acceptance intent, non-goals.
- PRD → scope: only an `APPROVED` product contract.
- Scope → plan: validated estimate, Goal packaging decision, dependency/conflict graph, and decision source.
- Plan → delivery: only `PLAN_APPROVED` artifacts with task IDs, dependencies, Goal/worktree/session ownership, gates, checkpoints, and completion criteria.
- Delivery → review: current revision IDs, clean commit, diff, test output, runtime evidence, model-routing records, deviations, and escalation packet.

## Progress continuity

Record four fixed denominators—implementation, automation, exact-target, and release—plus current activity, P50/P80 remaining estimate, and last progress time. Update durable progress after every attempt, invalidation, gate, checkpoint, routing mismatch, and wait transition. Record Goal-to-Goal inactivity as `coordination_wait`; do not report it as implementation time.

## Change ownership

Change only the plan for module layout, SDK behavior, task order, test mechanics, or another technical path that preserves the PRD.

Reopen the PRD for changed user flows, P0/P1 scope, product invariants, safety rules, data ownership, acceptance outcomes, release scope, or significant cost.

## Technical-change lane

Use the technical-change lane only after the user explicitly chooses `PRD_NOT_REQUIRED`. It is suitable for technical work whose observable product outcomes and governed boundaries remain unchanged. Record a bounded objective, constraints, acceptance checks, and rollback when relevant in the current task context; a PRD, scope assessment, Goal plan, and Program state are not prerequisites.

Execute with ordinary repository inspection, proportionate planning, local edits, tests, and verification. Do not invoke the PRD-dependent governed delivery skills or manufacture durable governance artifacts for ordinary maintenance.

If implementation reveals a change to user flows, P0/P1 scope, public contracts, product invariants, safety/compliance, data ownership, release scope, significant cost, or materially ambiguous acceptance, stop and return to `ROUTING_DECISION_PENDING`. The earlier `PRD_NOT_REQUIRED` decision does not authorize a wider product change.
