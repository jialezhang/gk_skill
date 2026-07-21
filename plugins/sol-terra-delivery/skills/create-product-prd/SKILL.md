---
name: create-product-prd
description: Use after product intent, scope, non-goals, and acceptance intent are sufficiently clear, and before implementation planning begins.
---

# Create Product PRD

Use one `gpt-5.6-sol` product author with `high` reasoning. Reserve `xhigh` for a documented product contradiction or unusually high-risk decision; document the reason in `model-routing.jsonl`.

Read these references completely before writing:

- [references/discovery-handoff.md](references/discovery-handoff.md)
- [references/prd-contract.md](references/prd-contract.md)
- [references/product-evidence.md](references/product-evidence.md)
- [references/quality-rubric.md](references/quality-rubric.md)

## Procedure

### Phase 1: Normalize discovery

1. Locate the active Spec Kit feature directory from `.specify/feature.json`, repository conventions, or an explicit path.
2. Convert the completed `grill-me` conversation into the discovery contract without discarding dissent, rejected options, or unresolved product choices.
3. If a missing answer would materially change user behavior, P0 scope, safety, authoritative data, release scope, or cost, ask the minimum focused product question and stop with `DISCOVERY_BLOCKED`.

### Phase 2: Ground the product

1. Read the constitution, existing product docs, relevant screens/routes, user-visible behavior, domain state, prior decisions, and incidents needed to understand the current product.
2. Distinguish observed evidence, user decisions, and technical assumptions. Never promote repository guesses into product requirements.
3. Record evidence paths or URLs beside claims that constrain the PRD.

### Phase 3: Draft

1. Use [assets/prd-template.md](assets/prd-template.md) to create or revise `spec.md`.
2. Define product concepts, state transitions, edge/failure behavior, invariants, requirements, non-goals, human decision boundaries, success metrics, and blocking acceptance journeys.
3. Give every core requirement a stable ID and observable acceptance mapping.
4. Keep implementation mechanisms out unless the user approved them as a product or organizational constraint.

### Phase 4: Independent review and revision

1. Use a fresh `gpt-5.6-luna` context for deterministic completeness, traceability, ambiguity, and acceptance-journey review. Give it the PRD, discovery handoff, and raw evidence—not the author's intended conclusion.
2. Use a second Sol reviewer only when Luna identifies a genuine product contradiction, safety decision, or unresolved high-risk judgment. Do not spend Sol on the same routine checklist twice.
3. Review against the quality rubric. Classify findings as `blocking`, `major`, or `minor` and assign each to discovery, PRD, or planning.
4. Resolve every blocking and major PRD-owned finding. Ask the user only for product-owned findings.
5. Run `python3 scripts/validate_prd.py <spec.md>` from this skill directory.
6. Set `prd_status: REVIEW_REQUIRED`. Do not set `APPROVED` yourself.
7. Present artifact path/version, material decisions, rejected options, remaining risks, and the exact approval boundary.

## Boundaries

- Keep model names, agent roles, Skills, file paths, task assignments, SDK versions, and code design out of the product contract.
- Include technical direction only when the user approved it as a product or organizational constraint; otherwise label it as a planning assumption.
- Do not proceed to planning while a product choice would materially change user behavior, P0 scope, safety, data ownership, release scope, or cost.
- Do not reward document length. Prefer precise product rules and executable acceptance over generic background prose.
