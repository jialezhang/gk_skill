# Verification Contract

## Delivery states

- `Implemented`: required code or configuration exists.
- `Enabled`: intended runtime can reach it.
- `Executed`: the approved target path ran on the identified build.
- `Verified`: evidence from that exact execution supports the acceptance claim.
- `Complete`: every blocking requirement is verified and no required work remains.

Never substitute one state for another.

## Required evidence layers

1. Focused automated checks for task behavior.
2. Integration checks for changed boundaries.
3. Exact-target acceptance for each blocking product journey.
4. Security, ownership, data, migration, and rollback evidence where relevant.
5. Lifecycle interruption and state-convergence evidence for asynchronous or event-driven journeys.
6. Diff review proving no unapproved architecture or scope was introduced.

## Acceptance case

Each real-target case records target identity, preconditions, user/owner, provider, build, flags, data, actions, observable UI/behavior, authoritative persisted facts, evidence paths, forbidden substitutions, and failure routing.

For a long-running journey, also record lifecycle identity and correlation keys, interruption point, injected event condition, expected authoritative state, every observed surface, convergence deadline, and whether stale UI actions can create duplicate side effects. At minimum cover:

- normal completion without manual refresh;
- reconnect or page restoration while work is nonterminal;
- dropped, delayed, duplicated, and out-of-order terminal updates;
- failure and cancellation;
- retry or replacement work superseding stale events;
- cross-surface agreement with the authoritative snapshot inside the declared convergence bound.

## Gates

At minimum define:

- readiness gate before speculative expansion;
- first 阶段真实用户旅程 gate;
- safety/data/migration gates when applicable;
- final exact-target acceptance gate.

Gate failure blocks downstream tasks whose assumptions depend on it. Ordinary local failures go back to the executor; baseline contradictions go to Sol; product-contract conflicts go to the user.

## Task done

A task is done only when its acceptance passes, focused checks pass, affected boundaries are exercised, relevant docs/state are updated, rollback is understood, deviations are recorded, and required evidence is attached. Task completion never implies product completion.
