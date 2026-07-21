# Gate Protocol

## Packet completeness

A gate packet includes gate/task IDs, artifact revisions, exact build/target identity, executor handoffs, raw test output, runtime evidence, diff summary, known failures/deferrals, rollback status, and relevant decision/escalation records.

## Review order

1. artifact and target identity;
2. prerequisite completion;
3. raw evidence validity;
4. product/architecture invariants;
5. security/data/migration/rollback obligations;
6. task acceptance and regression;
7. downstream assumption validity.

## Verdict rules

- `GATE_PASSED`: all required evidence supports the exact gate outcome.
- `REWORK_REQUIRED`: baseline remains valid; implementation/evidence needs repair.
- `PLAN_REVISED`: direct evidence changed the technical baseline and revision/invalidation is recorded.
- `PRODUCT_DECISION_REQUIRED`: every viable resolution changes the PRD.
- `VERIFICATION_BLOCKED`: exact target evidence cannot currently be obtained.

Do not return a mixed “mostly passed” verdict for a blocking gate.
