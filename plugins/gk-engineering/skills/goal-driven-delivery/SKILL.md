---
name: goal-driven-delivery
description: Use when an approved Goal plan is ready for implementation, recovery, or checkpointed verification after scope and model-routing preflight have passed.
---

# Goal-driven Delivery

Read these references completely before starting:

- [references/orchestration-contract.md](references/orchestration-contract.md)
- [references/state-machine.md](references/state-machine.md)
- [references/execution-packets.md](references/execution-packets.md)
- [references/executor-micro-loop.md](references/executor-micro-loop.md)
- [references/escalation-loop.md](references/escalation-loop.md)
- [references/verification-loop.md](references/verification-loop.md)
- [references/checkpoint-contract.md](references/checkpoint-contract.md)
- [references/project-profile-contract.md](references/project-profile-contract.md)
- [references/candidate-evidence-contract.md](references/candidate-evidence-contract.md)
- [references/browser-acceptance-contract.md](references/browser-acceptance-contract.md)
- [../product-to-delivery/references/native-agent-routing.md](../product-to-delivery/references/native-agent-routing.md)

## Preconditions

Require all of:

- `prd_status: APPROVED`;
- `plan_status: PLAN_APPROVED` and matching PRD version;
- `tasks_status: PLAN_APPROVED` and matching plan version;
- a defined exact target, rollback path, gates, and completion criteria;
- a validated `project-profile.json` declaring target components, protected resources, external effects, acceptance journeys, verification commands, and rollback actions;
- a validated scope assessment and selected Goal boundary;
- a passing Sol/Terra/Luna routing Canary, where an evidenced role-specific fallback on the current
  model satisfies unavailable slots and Terra fallback includes three failed raw attempts.

Return `DELIVERY_NOT_READY` if any condition is missing. Do not repair approval metadata implicitly.

## Start

1. Use the current visible Program task for a single Goal. For multiple Goals, keep Goal execution contexts internal by default and create another visible task only when the required model is unavailable on the native subagent surface. Record the exception as `VISIBLE_MODEL_CONTEXT_REQUIRED`. Do not set a token budget unless the user explicitly supplied one.
2. Use a dedicated worktree and branch for the Goal. Allocate an isolated development port/browser context when runtime verification is required; do not claim another Goal's runtime as exact-target evidence.
3. Run preflight: initialize and validate `project-profile.json`, then verify clean artifact revisions, repository target, worktree/branch, isolated runtime resources, rollback, verification commands, protected-resource boundaries, external-effect policies, program Agent budget, and absence of a second controller for this Goal. Define the runtime-provenance observations required for this target before any acceptance run; a configuration value or stored declaration is not runtime proof.
4. Require the active Program Goal and validated `program-state.yaml`; register this Goal as a milestone before initializing its state.
5. Initialize `delivery-state.yaml` from [assets/delivery-state-template.yaml](assets/delivery-state-template.yaml), pin the project Profile and artifact/scope revisions, and register every task, gate, checkpoint, Goal session, worktree, candidate manifest, progress denominator, and model-routing log before spawning work.
6. When the current main agent is already Terra, it may implement directly. Otherwise, before
   delegating implementation, debugging, local rework, or integration, make up to three sequential
   attempts to create a persistent Terra implementation context with explicit
   `model: "gpt-5.6-terra"`, no `agent_type`, and `fork_turns: "none"` or a positive limited-history
   value. Each spawn message must include `route_class: terra_implementation` and be a no-write
   `ROUTING HANDSHAKE ONLY` turn. Validate the original controller spawn call and the child runtime
   model. A route-guard nonce is optional supplemental evidence, not a prerequisite. On a denied
   spawn, missing raw evidence, model mismatch, hook mismatch, or unavailable route, quarantine and
   discard that context before the next attempt. After all three attempts fail, continue in the
   current model and record the attempts in `model-routing.jsonl`.

## Agent budget

The program owns one cumulative budget across all Goals: normal target 8, soft limit 12, and a hard limit of 20 spawned child Agents. Maximum nesting depth is 1 and maximum parallel Goal sessions is 3.

- Reuse the same Terra implementer for local fixes and the same Luna verifier for routine evidence.
- Do not create one Agent per task, verifier-of-verifier chains, or recursive orchestration.
- At 12, stop spawning optional reviewers and consolidate remaining work.
- At 20, reject every further spawn with `AGENT_BUDGET_EXHAUSTED`; do not reset the count per Goal or after an Agent exits.

## Delivery loop

1. Re-read Goal, approved revisions, repository state, and delivery state. Reconcile abandoned/running attempts before selecting work.
2. Compute the ready queue from dependencies and gates; do not trust task ordering in prose.
3. Open a bounded execution window using [references/executor-micro-loop.md](references/executor-micro-loop.md): select 1–3 ready tasks whose write scopes and consumed contracts do not conflict. Prefer one owner for coupled vertical work over artificial frontend/backend parallelism; three tasks is a maximum, not a quota.
4. Implement directly or reuse/spawn the preferred executor with explicit file/responsibility
   ownership and available program budget. Prefer the verified persistent `gpt-5.6-terra` context;
   after three failed raw switch attempts, the current main agent continues under
   `terra_route_fallback`. Do not replace Terra with a differently named child context or assume a
   role-pinned context proves the explicit model won.
5. Give each executor only the current execution packet: global MUST/FORBIDDEN IDs, task, consumed contract revisions, relevant prior evidence, write scope, verification, and escalation rules.
6. Require the executor to inspect actual code before editing, implement the smallest complete task outcome, run focused checks, inspect its diff, and return [assets/handoff-template.yaml](assets/handoff-template.yaml).
7. Reject handoffs that omit artifact revisions, actual verification output, deviations, or remaining risk.
8. Prefer an independent `gpt-5.6-luna` context for routine deterministic checks; when Luna is not
   exposed, use the current model under `luna_route_fallback`. Prefer an independent
   `gpt-5.6-terra` context for browser/runtime/final acceptance; after three failed raw Terra route
   attempts, use `terra_route_fallback`, with final acceptance in a fresh read-only context outside
   the implementation threads. Every browser operation uses Ego Lite `ego-browser` exclusively.
   Sol escalation likewise uses `sol_route_fallback` when unavailable.
9. Route results:
   - local failure → same executor or debugger;
   - cross-module integration failure → integration executor;
   - plan contradiction → pause affected tasks and invoke `$review-delivery-gate` with a Sol escalation packet; if Sol is unavailable, keep the current model and attach `sol_route_fallback` evidence;
   - product conflict → stop affected delivery and request user decision.
10. At each gate invoke `$review-delivery-gate` with exact evidence. Never let task completion implicitly pass a gate. Enforce every external-effect and protected-resource rule from the project Profile. A runtime target must have accepted provenance for the same candidate: preflight/launch, observed process or executor, build identity, target probe, and cleanup when applicable.
11. When an independently runnable 阶段真实用户旅程 or planned stage is complete, run the checkpoint contract: risk-appropriate verification, diff/protected-data checks, commit only owned files, push the Goal branch, then issue a progress report with the commit SHA and four fixed denominators. A checkpoint is not delivered if commit or push failed.
12. Close each execution window with its routed outcome and next action. Report checkpoints without treating routine feedback as an approval gate; when safe work remains, recompute the ready queue and continue.
13. Update state after every turn, execution window, attempt, review, gate, checkpoint, revision, and invalidation. Append routing records through plugin-root `scripts/append_routing_event.py --log <model-routing.jsonl> --event <event.json>` so an invalid or unknown event cannot mutate the durable log. Preserve history; do not overwrite failed evidence. Classify evidence as `draft`, `candidate`, `accepted`, `invalidated`, or `superseded`; record the invalidator and replacement when evidence can no longer support a gate.
14. Continue until all blocking requirements reach `Verified` on the exact target and independent
    Terra or audited Terra-fallback final acceptance passes on a clean commit, or an allowed Sol
    escalation is resolved.

## Delegated implementation route

Use this exact first-turn shape whenever code work is delegated:

```text
task_name: terra_implementation
model: gpt-5.6-terra
reasoning_effort: high
fork_turns: none
agent_type: omitted
message:
  route_class: terra_implementation
  ROUTING HANDSHAKE ONLY
```

The raw controller rollout must contain the matching native `spawn_agent` call, and the child
rollout must contain the requested `turn_context.payload.model`. These are the authoritative route
proof. When the optional native hook surface is active, the route guard also rejects an
implicit/wrong model, full-history fork, conflicting `agent_type`, or execution packet on the first
turn, records permission inheritance, and injects either:

- `SOL_TERRA_ROUTE_VERIFIED nonce=...` — preserve the echoed nonce as supplemental evidence;
- `SOL_TERRA_ROUTE_MISMATCH nonce=...` — quarantine and discard the context, then continue in the
  current main context with the model already in use.

A denied spawn, missing raw route evidence, or runtime model mismatch fails that attempt. A missing
nonce alone does not. Retry until three total attempts have failed, without parallel handshakes or
an unbounded loop. Then append an execution record with
`routing_surface: "main_agent"`, `model_selection_scope: "current_context"`,
`allowed_reason: "terra_route_fallback"`, the actual current model, and an ordered
`fallback_attempts` list containing three distinct Terra spawn identities and normalized failure
reasons. Runtime evidence must still prove every spawn attempt and the model that actually
performed each fallback execution turn.

When the route guard exposes permission changes, treat them as context-creation state and create a
new handshake context after a change. Do not synthesize permission fields on runtimes that do not
expose them. Reuse the verified Terra context while its model, Goal, and worktree remain unchanged.

## Recovery and persistence

- On continuation, inspect live agents before declaring an attempt abandoned.
- Reconcile repository changes with recorded attempt/worktree ownership.
- If artifact revisions changed, pause and run invalidation analysis before resuming.
- If the Goal remains active and safe work remains, continue; do not stop at a narrative checkpoint.
- Mark blocked only after the applicable Goal policy and repeated-blocker threshold are satisfied.

## Completion

For a multi-Goal Program, mark this milestone `GOAL_TARGET_VERIFIED` only after the exact clean commit, required 阶段真实用户旅程, every checkpoint, model routing, candidate evidence, and fixed progress denominators validate. Do not call the runtime Goal completion tool.

Only the Program controller may mark the runtime Program Goal complete. Before the terminal Goal transition, collect and persist a completion telemetry snapshot: observed token/time totals by model and stage, source paths, and explicit `unavailable` fields. Use `scripts/collect_delivery_telemetry.py --completion-snapshot --output <snapshot>` when rollout telemetry is available; never estimate missing model usage. Record that snapshot in `delivery-state.yaml` before changing the runtime Goal state.

Immediately after the snapshot and before the terminal transition, keep the Goal at `GOAL_TARGET_VERIFIED` and the Program at `PROGRAM_TARGET_VERIFIED`. Run `scripts/validate_completion_gate.py` from the plugin root with `--receipt <completion-receipt.json>`, the project Profile, routing log, Goal delivery state, candidate evidence, and Program state; include the integration manifest for a multi-Goal Program. The command writes the receipt atomically only after the raw rollout, Canary, transition, handshake, runtime provenance, evidence lifecycle, Profile and completion telemetry all validate. Re-run `scripts/validate_completion_receipt.py <completion-receipt.json>` immediately before completion to prove no input changed. A declared status, model name, boolean, or stale receipt never substitutes for this transaction.

After receipt revalidation, record its path and digest in both states, transition them to `COMPLETE`, and only then may the Program controller mark the runtime Program Goal complete. Preserve the receipt and invoke `$goal-retrospective`. Provide the approved artifacts, all Goal and integration evidence, accepted candidate identity, routing and telemetry records, invalid runs, final acceptance, and the completion receipt. The retrospective is a post-completion audit and cannot substitute for this gate or change the recorded Goal status. If the document cannot be written, report `RETROSPECTIVE_PENDING` with the missing evidence or recovery action.
