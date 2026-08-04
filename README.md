# GK Engineering — Sol–Terra Spec-Driven Delivery Toolkit

An installable Codex plugin and Spec Kit customization for this lifecycle:

```text
request with no approved PRD
→ ask whether a PRD is needed
├─ PRD_NOT_REQUIRED → lightweight technical-change lane → implement, test, verify
└─ PRD_REQUIRED
   → $grill-me
   → $create-product-prd
   → user approves PRD
   → $assess-goal-scope
   → user chooses split or single Goal (240s silence defaults to single)
   → $create-implementation-plan
   → user approves plan
   → verified Sol/Terra/Luna routing Canary (audited current-model fallback when Sol is unavailable)
   → one or more $goal-driven-delivery sessions/worktrees
   → checkpoint commit + push + progress report
   → $integrate-goals when delivery was split
   → verified final acceptance
   → runtime Goal completion receipt
   → $goal-retrospective auditable post-completion review
```

The toolkit keeps the two control planes separate:

- Spec Kit owns durable artifacts: `spec.md`, `plan.md`, `tasks.md`, approvals, and traceability.
- Codex owns live execution: one controller per Goal, a program-level dependency/Agent budget, isolated worktrees/sessions, retries, integration, and completion.

It does not replace the existing `grill-me` skill. The PRD skill consumes the completed conversation or a discovery artifact. The implementation-plan skill is a new, standalone toolkit skill whose planning method is based on the custom planning work in [`jialezhang/skill`](https://github.com/jialezhang/skill/tree/main).

## Install the Codex plugin

From this repository root:

```bash
codex plugin marketplace add .
codex plugin add gk-engineering@gk-skill
```

Restart Codex after installation so the eight skills are discovered.

## Install the Spec Kit layer into a project

Install Spec Kit first if `specify` is unavailable:

```bash
uv tool install specify-cli
```

Then run:

```bash
python3 plugins/gk-engineering/scripts/install.py \
  --project /absolute/path/to/project \
  --init-spec-kit
```

The installer adds the local preset, governance extension, and pre-delivery workflow. It does not start delivery or approve either gate.

## Use it

The initial recommended surface is explicit stage commands:

```text
$grill-me

$create-product-prd
Use the completed discovery above. Write the PRD into the current Spec Kit feature.

# After reviewing and explicitly approving the PRD:
$assess-goal-scope

$create-implementation-plan

# After reviewing and explicitly approving plan.md and tasks.md:
$goal-driven-delivery

# After the governed Program Goal completes, the controller invokes this automatically:
$goal-retrospective
```

`$product-to-delivery` is the convenience controller. When no approved PRD exists and the request can remain a technical change, it first asks whether a PRD is needed and gives a recommendation. An explicit `PRD_NOT_REQUIRED` choice enters a lightweight technical-change lane without Spec Kit governance artifacts. The governed lane still pauses at both human approval gates. Silence never chooses the PRD lane, skips a PRD, or approves a PRD/plan. The only timed default is Goal packaging: after a 240-second unanswered split prompt, delivery remains one Goal and records `timeout_default_single`.

## Delivery policy

- Technical changes may bypass PRD creation only after the user explicitly chooses `PRD_NOT_REQUIRED`; if product or governed risk boundaries emerge, the controller reclassifies before continuing.
- Scope is inspected before planning. P80 above 8 hours recommends splitting; above 10 hours strongly recommends it. Users may still choose one Goal.
- Sol is preferred for PRD, scope, planning, and genuine product/plan/architecture/high-risk security conflicts. If Sol is unavailable, the current main model continues under audited `sol_route_fallback`; Goal work does not block on Sol availability.
- Terra handles delivery control, implementation, debugging, rework, and integration.
- Luna handles routine checks and build/checklist review.
- Terra judges browser E2E, stage journeys, runtime boundaries, and final acceptance. Every browser interaction and browser evidence is produced exclusively through Ego Lite `ego-browser`.
- Model selection is explicit on every turn. Runtime metadata—not an Agent name or self-report—must prove the observed model. A mismatch fails closed.
- The normal Agent target is 8, soft limit 12, cumulative hard limit 20, maximum nesting depth 1, and at most 3 parallel Goal sessions.
- Each runnable stage ends with focused checks, an owned-file commit, verified push, and a fixed-denominator progress report.
- Multi-Goal delivery is accepted only after a clean integration commit passes the complete approved verification path.
- After the runtime Program Goal completes, `$goal-retrospective` reconciles the completion receipt, approved plan, delivery evidence, invalid runs, Git/runtime identity, time/Token口径, and next-cycle actions. It is a post-completion audit, not an acceptance gate.

## Skill depth

The entry `SKILL.md` files are intentionally short routing surfaces. They are not the whole implementation. Each stage loads its detailed protocol from `references/`, instantiates output shapes from `assets/`, and runs deterministic checks from `scripts/`. This keeps unrelated instructions out of the active context without reducing delivery rigor.

| Skill | Full procedure behind the entry point |
| --- | --- |
| `$product-to-delivery` | Lifecycle state detection, approval protocol, stage routing, recovery, and Sol/Terra authority boundaries |
| `$create-product-prd` | Discovery normalization, repository and user evidence, product-state modeling, requirement metadata, independent review, and deterministic PRD validation |
| `$assess-goal-scope` | Repository-based work packages, P50/P80/P90 sizing, split recommendation, timeout decision, dependency/conflict graph, and Goal boundary handoff |
| `$create-implementation-plan` | Direction readiness, architecture and ownership contracts, complete milestone/task baseline, dependency graph, delegation map, exact-target verification, independent plan review, and cross-artifact validation |
| `$goal-driven-delivery` | Per-Goal Terra ownership, worktree/session isolation, ready-queue scheduling, 20-Agent hard cap, per-turn routing records, checkpoint commits, retries, gates, and restart recovery |
| `$integrate-goals` | Clean integration worktree, ordered Goal merge, conflict routing, full verification, Luna acceptance, and cross-session evidence/telemetry aggregation |
| `$review-delivery-gate` | Luna routine evidence review, Terra code-quality review, Sol escalation classification, exact-target acceptance, and final PRD-to-runtime reconciliation |
| `$goal-retrospective` | Post-completion Goal identity and cost reconciliation, actual-stage reconstruction, invalid-run accounting, plan/acceptance audit, and executable next-cycle rules |

The planning skill is therefore not a reduced replacement for the earlier planning work. It preserves the high-value readiness, responsibility-replacement, verification, rollback, and Legacy-exit methods, while removing repeated prose and treating unsupported implementation guesses as `VERIFY_FIRST` rather than facts.

The optional Spec Kit workflow prepares PRD, scope, plan, tasks, and verification artifacts only:

```bash
specify workflow run sol-terra-pre-delivery \
  --input feature="Describe the feature"
```

The workflow uses the integration's current model. The stage skills prefer Sol when it is live and otherwise record `sol_route_fallback`, so an unavailable Sol route cannot prevent Goal delivery.

Do not use that external workflow and `$goal-driven-delivery` as concurrent implementation controllers. Delivery is owned by the Codex skill.

## Validate the package

```bash
python3 plugins/gk-engineering/scripts/validate_toolkit.py
```

The validator checks the plugin, all skills, Spec Kit manifests, templates, and cross-file IDs. A full smoke test additionally installs the Spec Kit components into a disposable initialized project.
