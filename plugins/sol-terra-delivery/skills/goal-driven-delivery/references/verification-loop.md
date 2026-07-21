# Verification Loop

## Separation of duties

- Executor produces implementation and focused self-check evidence.
- Independent verifier executes planned checks and challenges target identity.
- Luna independently executes routine checks and decides uncomplicated gate/final acceptance from the approved criteria.
- Sol decides only escalated product, plan, architecture, or high-risk security contradictions.

## Verification sequence

1. confirm artifact revisions, model-routing records, and exact clean build/commit;
2. confirm requested target identity, user/owner, flags, data, and providers;
3. run focused automated checks;
4. run changed integration boundaries;
5. run required regression/static checks;
6. execute exact-target journey where the gate requires it;
7. inspect authoritative persisted facts and user-visible results;
8. attach raw outputs/screenshots/logs and record unexecuted checks;
9. compare diff with scope and forbidden constraints.
10. confirm the checkpoint commit is pushed and its progress report is recorded.

## Failure routing

- Behavior wrong, contract unchanged → local rework.
- Test invalid or flaky → test-engineer repair, then rerun.
- Evidence contradicts baseline → plan escalation.
- Exact target unavailable → verification blocked; do not substitute.
- Product acceptance impossible without changed outcome → user decision.
