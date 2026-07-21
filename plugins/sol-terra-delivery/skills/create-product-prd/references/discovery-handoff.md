# Discovery Handoff

Normalize `grill-me` output into this logical structure. It may remain embedded in the conversation, but a durable `discovery.md` is preferred for long work.

```yaml
status: DISCOVERY_READY | DISCOVERY_BLOCKED
problem:
  target_user:
  current_pain:
  evidence: []
desired_outcome:
primary_journeys: []
must_have: []
non_goals: []
product_invariants: []
confirmed_decisions: []
rejected_options: []
acceptance_intent: []
product_risks: []
technical_assumptions: []
open_product_questions: []
```

## Readiness test

Discovery is ready when the primary user and problem, target outcome, main journey, must-have scope, explicit exclusions, major product trade-offs, and visible success are sufficiently clear to write testable requirements.

Do not require answers to implementation questions that repository inspection or experimentation can resolve later.

## Conflict handling

When conversation statements conflict, preserve both statements, identify the decision that owns the conflict, and ask one focused question. Never silently choose the most recent or most detailed sentence when the product impact differs.
