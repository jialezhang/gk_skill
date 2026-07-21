# Sizing Contract

## Meaning of P80

P80 is a calibrated wall-clock estimate: 80% of comparable deliveries should finish within it. Track active execution separately when reporting cost. For parallel Goals, wall-clock P80 is the longest dependency path plus integration and verification, not the sum of every worker's hours.

## Evidence basis

Build estimates from work packages and repository inspection. Each package records:

- observable outcome and exact-target proof;
- optimistic, P50, P80, and conservative duration;
- likely files and system domains;
- dependencies and write conflicts;
- environment, migration, authorization, data, or lifecycle uncertainty;
- integration and retry allowance.

Use historical actuals when available. Otherwise use ranges and state confidence. False precision is a finding: do not claim decimal-hour confidence without calibrated data.

## Split quality

A proposed Goal must have an independently reviewable outcome, bounded write scope, focused verification, worktree/branch, session owner, and checkpoint commit. Splits that merely separate frontend from backend while sharing unstable contracts are unsafe.

The scope assessment recommends packaging; the implementation plan owns the final task DAG inside the selected Goal structure.
