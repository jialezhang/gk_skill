# PRD Quality Rubric

The independent reviewer evaluates each dimension and reports evidence-backed findings.

## Product clarity

- The target user, problem, outcome, and primary journey are concrete.
- The PRD distinguishes current behavior from desired behavior.
- Product concepts and terms have one stable meaning.

## Scope integrity

- P0/P1 requirements, non-goals, and invariants do not contradict one another.
- Edge and failure behavior is defined where it affects users.
- The document does not smuggle implementation preferences into product scope.

## Decision completeness

- Product trade-offs are explicit.
- Rejected options and material reasons are preserved.
- Technical unknowns are labeled for planning rather than guessed.
- Human decision boundaries are actionable.

## Testability

- Every core requirement is observable.
- Every blocking journey maps to expected evidence.
- Completion cannot be satisfied by mock, fallback, adjacent, or legacy behavior unless approved.
- Success metrics measure outcomes rather than document/task completion.

## Delivery fitness

- A fresh planner can identify what must remain stable and what is free to design.
- A final reviewer can determine whether the product was built correctly without reconstructing discovery.
- Change-control rules distinguish plan revision from PRD revision.

## Severity

- `blocking`: ambiguity or contradiction can change the product, safety, data, core scope, or completion.
- `major`: a core requirement, journey, state, failure, or acceptance mapping is missing or not testable.
- `minor`: clarity or organization issue that does not change delivery decisions.

The PRD may enter `REVIEW_REQUIRED` only when no blocking or major PRD-owned finding remains.
