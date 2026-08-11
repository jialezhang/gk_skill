# Planning Contract

This method is adapted from the readiness, decomposition, and verification ideas in `jialezhang/skill` at commit `08fe84459111fbd1fafcae048c0052332ffd1def`.

## Readiness

Do not infer a rewrite from a list of local defects. For each issue classify:

- `local fix`: the current design can satisfy the requirement through bounded repair.
- `compatible extension`: the current design remains valid but needs an additive contract.
- `incompatible constraint`: a proven limitation prevents the approved outcome.

Return `READINESS_BLOCKED` if decisive repository, dependency, safety, or runtime evidence is missing. Convert discoverable uncertainty into a front-loaded verification task rather than a user question.

## Target identity

Freeze the exact product/module, entry point, routes, services, repositories, stores, flags, build, user/owner scope, and real providers that count as acceptance. Legacy routes, mocks, fixtures, fallback providers, and adjacent capabilities are diagnostic unless explicitly approved as the target.

## Commitment levels

| Level | Executor rule |
| --- | --- |
| `MUST` | Preserve. Only the user may change a product contract; technical MUSTs may be revised when authorized evidence requires it, preferring Sol and otherwise using `sol_route_fallback`. |
| `BASELINE` | Follow by default. A direct repository or runtime contradiction requires revision through the planning stage, preferring Sol and otherwise using the current model. |
| `VERIFY_FIRST` | Test before dependent implementation; never treat as established fact. |
| `RECOMMENDED` | Use unless a simpler equivalent local choice preserves all contracts. Record deviations. |
| `DEFERRED` | Decide at the named gate using the written decision rule. |
| `FORBIDDEN` | Do not implement without plan or product revision as specified. |

## Full baseline without false precision

Plan all milestones and major tasks before approval so another model can continue coherently. For distant tasks specify outcome, contracts, dependencies, acceptance, role, risks, and decision inputs. Add exact files, APIs, function shapes, and commands only when already grounded by repository evidence or an earlier verification task.

## Responsibility replacement

For migrations or new runtimes, map:

```text
current responsibility → current owner → new owner → handoff condition → legacy disposition
```

Do not allow two permanent owners for the same runtime state or business fact.

## Runtime lifecycle and state convergence

For asynchronous or event-driven work, model interaction, command, business-work, persistence, and presentation lifecycles separately. A terminal state in one lifecycle must not terminate another unless the plan proves they are coextensive.

The plan must define:

- one authoritative owner and terminal-state vocabulary for each business operation;
- stable correlation and ordering keys across commands, runs, jobs, events, snapshots, retries, and user-visible projections;
- subscription lifetime based on the authoritative business operation rather than an interaction, request, transport, or page lifecycle;
- an authoritative snapshot and reconciliation triggers for initial load, reconnect, event gaps, visibility changes, and periodic recovery while work is nonterminal;
- idempotent handling for duplicate, delayed, out-of-order, and superseded events;
- a bounded convergence objective shared by every surface that displays the same fact;
- stale-action protection so an obsolete projection cannot cause duplicate, conflicting, or chargeable work.

Use events to reduce display latency; do not make successful event delivery the sole correctness mechanism unless durable replay and gap recovery are verified on the exact target.

## Task contract

Every task must include:

- observable outcome and requirement IDs;
- dependencies and gate membership;
- relevant constraint/decision IDs;
- preferred role and bounded write scope;
- acceptance and focused verification;
- exact-target handoff when applicable;
- rollback or disable behavior when risky;
- replanning/escalation triggers;
- optional, non-binding candidate touchpoints.

Tasks that create, alter, or consume asynchronous state must also name the lifecycle identities, authoritative status, convergence/recovery obligation, and fault-oriented verification they own.

## Delegation

The current main planning agent recommends role, skills, write scope, parallel safety, and review owner, preferring Sol and otherwise recording `sol_route_fallback`. Terra schedules according to dependencies and current evidence. Parallelize only when contracts are frozen and write scopes do not overlap.

## Plan revision

When execution disproves a baseline assumption, rerun the planning stage, preferring Sol and otherwise using the current model under `sol_route_fallback`. Change only the affected plan/tasks, increment the plan revision, record the decisive evidence, and invalidate downstream task attempts that consumed the old contract. A technical revision that changes the PRD must stop for user approval before the PRD is revised.
