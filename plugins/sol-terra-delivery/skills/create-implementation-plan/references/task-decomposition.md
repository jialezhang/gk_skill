# Task Decomposition Protocol

## Requirement traceability first

Create a matrix before tasks:

```text
requirement → journey → milestone → task(s) → automated evidence → exact-target case → gate
```

Every P0/P1 requirement must have work and evidence. Every task must trace to an approved requirement, risk reduction, migration, verification, or cleanup obligation.

## Vertical task rule

Prefer observable vertical outcomes over layer-only work. A foundational task is justified only when downstream tasks consume a named contract and its verification can fail independently.

## Complete baseline rule

Plan all approved milestones and major tasks before user approval. Distant tasks still need outcome, dependencies, contracts, acceptance, risks, delegation, and decision inputs. Avoid unsupported function names, exact files, API signatures, or abstraction counts.

## Task fields

Required:

- stable ID and observable outcome;
- requirement/journey/risk IDs;
- dependencies and consumed contract versions;
- relevant MUST/FORBIDDEN IDs;
- preferred role and required skills;
- bounded write scope and shared-file warnings;
- acceptance and focused/integration verification;
- exact-target handoff when applicable;
- rollback or disable path when risky;
- evidence destination;
- escalation and replanning triggers.

Conditional:

- candidate touchpoints when repository evidence supports them;
- migration safety for schemas/data;
- Legacy disposition for replacements;
- documentation changes for public/operational contracts;
- commit boundary for high-risk or parallel work.
- lifecycle identities, state-transition ownership, correlation/order keys, subscription/reconciliation behavior, and fault-injection checks for asynchronous or event-driven work.

## Lifecycle-boundary rule

Do not hide a long-running journey inside layer-only tasks that separately implement “dispatch”, “events”, and “UI state” without an owning integration task. Add a vertical task and gate that prove the authoritative operation remains observable through interruption and that every affected surface converges without duplicate side effects.

## Parallel plan

Tasks may run concurrently only when dependencies are satisfied, shared contracts are frozen, write scopes do not overlap, and integration order is explicit. A parallel marker is permission, not an instruction to maximize concurrency.

## Gate placement

Place a gate after evidence-producing clusters, especially compatibility probes, the first real slice, security/data migration, and release cutover. Do not add ceremonial gates that only restate task completion.
