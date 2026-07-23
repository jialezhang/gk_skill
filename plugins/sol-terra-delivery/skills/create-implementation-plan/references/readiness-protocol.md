# Readiness Protocol

## Evidence order

1. Approved PRD and constitution.
2. Repository rules and current implementation.
3. Existing tests and runtime configuration.
4. Decisions, incidents, migrations, and product evidence.
5. Official dependency/API documentation when an external contract matters.

## Required readiness sections

- exact target identity;
- current-state evidence map;
- problem/change classification;
- responsibility owner map;
- authoritative data and identity path;
- runtime lifecycle and state-convergence map when work can outlive an interaction, request, connection, process, or page;
- compatibility and migration obligations;
- first 阶段真实用户旅程;
- falsifiers, stop actions, and recovery owner.

## Rewrite challenge

For a rewrite, replacement runtime, new persistence layer, or new domain model, answer:

1. Which approved outcome cannot the current design satisfy?
2. What direct evidence proves the incompatibility?
3. Which responsibility moves, and which Legacy responsibility can be removed?
4. What is the smallest reversible proof before expansion?
5. What happens if the assumption is false?

If these cannot be answered, plan verification instead of replacement.

## Status

- `READY`: sufficient evidence exists to define a complete baseline.
- `READINESS_BLOCKED`: a necessary product/authority/external fact cannot currently be obtained.
- `READINESS_REVIEW_REQUIRED`: task decomposition exposes a contradiction in target identity, ownership, or direction; return to readiness.

Do not use `READINESS_BLOCKED` for ordinary engineering uncertainty that experiments can resolve.

## Asynchronous lifecycle readiness

When any user-visible work may continue after an interaction, request, command, connection, process, or page ends, establish before planning:

1. the distinct interaction, command, business-work, persistence, and presentation identities and their correlation keys;
2. the single authoritative owner and terminal-state definition for the business work;
3. which states only mean “accepted”, “dispatched”, or “waiting” and therefore must not terminate observation;
4. the authoritative snapshot used to recover after reconnect or event loss;
5. every consumer surface and its convergence mechanism, bound, and stale-action risk.

Treat events as latency optimizations unless the system provides durable replay with an established recovery contract. A UI subscription or interaction status is not an authoritative business-state owner.
