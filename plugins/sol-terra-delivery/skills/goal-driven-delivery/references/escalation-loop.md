# Escalation Loop

## Local implementation issue

Terra owns reversible differences that preserve product, public contracts, safety, data ownership, architecture baseline, task scope, and acceptance. Examples: actual file location, existing helper reuse, naming, local refactor, test mechanics, and fixable implementation defects.

## Plan-level conflict

Pause affected tasks and escalate to Sol when evidence requires:

- changing a BASELINE/MUST technical decision;
- adding a state owner, runtime, persistence layer, domain object, or public contract;
- changing dependency order or responsibility transfer materially;
- violating a FORBIDDEN constraint;
- expanding into another milestone;
- changing migration, idempotency, compatibility, or rollback semantics;
- using a fallback/Legacy route to satisfy target acceptance.

The controller assembles one evidence packet. Child agents do not ask the user or independently negotiate architecture.

## Product-level conflict

Sol consolidates options and asks the user only when every viable plan changes user behavior, P0/P1 scope, product invariants, non-goals, safety, authoritative data, completion, release scope, or significant cost.

## Resume after revision

1. record the new plan revision and decision;
2. identify consumed contracts that changed;
3. mark affected attempts/gates stale;
4. regenerate execution packets;
5. rerun only invalidated implementation or evidence;
6. continue the Goal.
