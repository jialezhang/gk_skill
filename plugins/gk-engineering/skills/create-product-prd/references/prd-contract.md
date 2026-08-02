# Agent-ready PRD Contract

## Required properties

The PRD must let a fresh planner and a final acceptance reviewer answer:

1. Who is the user and what problem is being solved?
2. What must the user be able to observe?
3. Which invariants and non-goals cannot be traded away?
4. Which decisions can delivery make autonomously?
5. Which changes require the user to approve a new PRD revision?
6. Which real journeys block completion?

## Approval metadata

Use a machine-readable header containing:

```yaml
prd_status: DRAFT | REVIEW_REQUIRED | APPROVED | CHANGE_REQUESTED | SUPERSEDED
prd_version: semver
approved_by: null | user
approved_at: null | ISO-8601 timestamp
approval_scope:
  product_outcome: pending | approved
  requirements: pending | approved
  non_goals: pending | approved
  acceptance: pending | approved
```

Only explicit user approval may set `APPROVED`.

## Requirement metadata

Every requirement needs a stable ID, priority, domain, risk, acceptance type, and human-decision rule. Domains describe product/engineering surfaces, not agent identities.

Recommended acceptance types: `automated`, `browser`, `integration`, `data`, `security`, `real-target`.

## Decision boundary

Delivery may autonomously make reversible internal choices that preserve the PRD. It must ask the user before changing the core journey, P0/P1 scope, safety or confirmation rules, authoritative data owner, completion criteria, release scope, or significant cost.

## Completion

A PRD is ready for planning when all blocking product choices are resolved, core journeys and non-goals are explicit, requirements are testable, and completion is defined. Technical unknowns that repository exploration or experiments can answer remain planning inputs, not product blockers.
