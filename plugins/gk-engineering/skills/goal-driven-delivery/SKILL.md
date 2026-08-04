---
name: goal-driven-delivery
description: Use when an approved Goal plan is ready for implementation, recovery, or checkpointed verification after scope and model-routing preflight have passed.
---

# Goal-driven Delivery

Read these references completely before starting:

- [references/orchestration-contract.md](references/orchestration-contract.md)
- [references/state-machine.md](references/state-machine.md)
- [references/execution-packets.md](references/execution-packets.md)
- [references/escalation-loop.md](references/escalation-loop.md)
- [references/verification-loop.md](references/verification-loop.md)
- [references/checkpoint-contract.md](references/checkpoint-contract.md)
- [references/candidate-evidence-contract.md](references/candidate-evidence-contract.md)
- [references/browser-acceptance-contract.md](references/browser-acceptance-contract.md)
- [../product-to-delivery/references/native-agent-routing.md](../product-to-delivery/references/native-agent-routing.md)

## Preconditions

Require all of:

- `prd_status: APPROVED`;
- `plan_status: PLAN_APPROVED` and matching PRD version;
- `tasks_status: PLAN_APPROVED` and matching plan version;
- a defined exact target, rollback path, gates, and completion criteria;
- a validated scope assessment and selected Goal boundary;
- a passing Sol/Terra/Luna routing Canary, where an evidenced `sol_route_fallback` on the current model satisfies only unavailable Sol slots;
- explicit user authorization to execute and use subagents.

Return `DELIVERY_NOT_READY` if any condition is missing. Do not repair approval metadata implicitly.

## Start

1. Use the current visible Program task for a single Goal. For multiple Goals, keep Goal execution contexts internal by default and create another visible task only when the required model is unavailable on the native subagent surface. Record the exception as `VISIBLE_MODEL_CONTEXT_REQUIRED`. Do not set a token budget unless the user explicitly supplied one.
2. Use a dedicated worktree and branch for the Goal. Allocate an isolated development port/browser context when runtime verification is required; do not claim another Goal's runtime as exact-target evidence.
3. Run preflight: verify clean artifact revisions, repository target, worktree/branch, ports, rollback, verification commands, protected-data boundaries, program Agent budget, and absence of a second controller for this Goal. Define the runtime-provenance observations required for this target before any acceptance run; a configuration value or database row is not runtime proof.
4. Require the active Program Goal and validated `program-state.yaml`; register this Goal as a milestone before initializing its state.
5. Initialize `delivery-state.yaml` from [assets/delivery-state-template.yaml](assets/delivery-state-template.yaml), pin artifact/scope revisions, and register every task, gate, checkpoint, Goal session, worktree, candidate manifest, progress denominator, and model-routing log before spawning work.
6. When the current main agent is already Terra, it may implement directly. Otherwise, before delegating implementation, debugging, local rework, or integration, make up to three sequential attempts to create a persistent Terra implementation context with explicit `model: "gpt-5.6-terra"`, no `agent_type`, and `fork_turns: "none"` or a positive limited-history value. Each spawn message must include `route_class: terra_implementation` and be a no-write `ROUTING HANDSHAKE ONLY` turn. Never use a full-history fork or a role profile that can override the explicit model. The bundled route guard verifies each attempt's actual `SubagentStart.model`, inherited `permission_mode`, and one-time nonce before an execution packet is sent. On a denied spawn, missing verification marker, model/permission mismatch, hook error, or unavailable route, quarantine and discard that delegated context before the next attempt. If any attempt succeeds, reuse it. Only after all three attempts fail, continue the implementation in the current main context using its existing model and record all three attempts in `model-routing.jsonl`.

## Agent budget

The program owns one cumulative budget across all Goals: normal target 8, soft limit 12, and a hard limit of 20 spawned child Agents. Maximum nesting depth is 1 and maximum parallel Goal sessions is 3.

- Reuse the same Terra implementer for local fixes and the same Luna verifier for routine evidence.
- Do not create one Agent per task, verifier-of-verifier chains, or recursive orchestration.
- At 12, stop spawning optional reviewers and consolidate remaining work.
- At 20, reject every further spawn with `AGENT_BUDGET_EXHAUSTED`; do not reset the count per Goal or after an Agent exits.

## Delivery loop

1. Re-read Goal, approved revisions, repository state, and delivery state. Reconcile abandoned/running attempts before selecting work.
2. Compute the ready queue from dependencies and gates; do not trust task ordering in prose.
3. Select tasks whose write scopes and consumed contracts do not conflict. Prefer one owner for coupled vertical work over artificial frontend/backend parallelism.
4. Implement directly or reuse/spawn the preferred executor with explicit file/responsibility ownership and available program budget. A delegated implementation, debugging, local rework, or integration subagent must use the verified persistent `gpt-5.6-terra` context. If that one switch attempt fails, the current main agent continues directly with its existing model; do not replace Terra with a differently named child context. Do not create `team-executor`, `executor`, `worker`, or another role-pinned context and assume the explicit model won.
5. Give each executor only the current execution packet: global MUST/FORBIDDEN IDs, task, consumed contract revisions, relevant prior evidence, write scope, verification, and escalation rules.
6. Require the executor to inspect actual code before editing, implement the smallest complete task outcome, run focused checks, inspect its diff, and return [assets/handoff-template.yaml](assets/handoff-template.yaml).
7. Reject handoffs that omit artifact revisions, actual verification output, deviations, or remaining risk.
8. Assign routine focused checks, typecheck, build, diff checks, baseline comparison, and checklist reconciliation to an independent `gpt-5.6-luna` context. Assign browser acceptance, 阶段真实用户旅程, runtime lifecycle/Provider-boundary acceptance, and final exact-target acceptance to an independent `gpt-5.6-terra` context. Every browser operation in those stages must use Ego Lite `ego-browser` exclusively and satisfy the browser acceptance contract. Sol is preferred only for an allowed product, plan, architecture, or high-risk security escalation; when unavailable, the current model handles that escalation under `sol_route_fallback` without blocking the Goal.
9. Route results:
   - local failure → same executor or debugger;
   - cross-module integration failure → integration executor;
   - plan contradiction → pause affected tasks and invoke `$review-delivery-gate` with a Sol escalation packet; if Sol is unavailable, keep the current model and attach `sol_route_fallback` evidence;
   - product conflict → stop affected delivery and request user decision.
10. At each gate invoke `$review-delivery-gate` with exact evidence. Never let task completion implicitly pass a gate. A runtime target must have accepted provenance for the same candidate: preflight/launch, observed process or executor, build identity, target probe, and cleanup when applicable.
11. When an independently runnable 阶段真实用户旅程 or planned stage is complete, run the checkpoint contract: risk-appropriate verification, diff/protected-data checks, commit only owned files, push the Goal branch, then issue a progress report with the commit SHA and four fixed denominators. A checkpoint is not delivered if commit or push failed.
12. Update state and `model-routing.jsonl` after every turn, attempt, review, gate, checkpoint, revision, and invalidation. Preserve history; do not overwrite failed evidence. Classify evidence as `draft`, `candidate`, `accepted`, `invalidated`, or `superseded`; record the invalidator and replacement when evidence can no longer support a gate.
13. Continue until all blocking requirements reach `Verified` on the exact target and independent Terra final acceptance passes on a clean commit, or an allowed Sol escalation is resolved.

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

The `PreToolUse: Agent` hook rejects an implicit/wrong model, full-history fork, conflicting
`agent_type`, or an execution packet sent on the first turn. It records the parent
`permission_mode`. Only one Terra switch may be pending per parent session at a time; attempts two
and three start only after the prior context has failed and been discarded. Pending state expires
after 60 seconds so an abandoned spawn cannot consume a later subagent start. The `SubagentStart`
hook compares the actual model and inherited permission mode, then injects either:

- `SOL_TERRA_ROUTE_VERIFIED nonce=...` — require the subagent to echo the exact nonce before
  sending work through `followup_task`;
- `SOL_TERRA_ROUTE_MISMATCH nonce=...` — quarantine and discard the context, then continue in the
  current main context with the model already in use.

A denied spawn or a handshake turn that returns without the matching verified nonce fails that
attempt. Retry until three total attempts have failed, without parallel handshakes or an unbounded
loop. Then append an execution record with
`routing_surface: "main_agent"`, `model_selection_scope: "current_context"`,
`allowed_reason: "terra_route_fallback"`, the actual current model, and an ordered
`fallback_attempts` list containing three distinct Terra spawn identities and normalized failure
reasons. Runtime evidence must still prove every spawn attempt and the model that actually
performed each fallback execution turn.

Permission changes are applied at context creation. If the user changes the main thread's
permission mode, stop the old Terra context and create a new handshake context; do not assume an
existing subagent was upgraded retroactively. Reuse the verified Terra context for later code
tasks while its model, permission mode, Goal, and worktree remain unchanged.

## Recovery and persistence

- On continuation, inspect live agents before declaring an attempt abandoned.
- Reconcile repository changes with recorded attempt/worktree ownership.
- If artifact revisions changed, pause and run invalidation analysis before resuming.
- If the Goal remains active and safe work remains, continue; do not stop at a narrative checkpoint.
- Mark blocked only after the applicable Goal policy and repeated-blocker threshold are satisfied.

## Completion

For a multi-Goal Program, mark this milestone `GOAL_TARGET_VERIFIED` only after the exact clean commit, required 阶段真实用户旅程, every checkpoint, model routing, candidate evidence, and fixed progress denominators validate. Do not call the runtime Goal completion tool.

Only the Program controller may mark the runtime Program Goal complete. Before the terminal Goal transition, collect and persist a completion telemetry snapshot: observed token/time totals by model and stage, source paths, and explicit `unavailable` fields. Use `scripts/collect_delivery_telemetry.py --completion-snapshot --output <snapshot>` when rollout telemetry is available; never estimate missing model usage. Record that snapshot in `delivery-state.yaml` before changing the runtime Goal state.

Immediately after the snapshot and before the terminal transition, run `scripts/validate_completion_gate.py` from the plugin root with the routing log, Goal delivery state, candidate evidence, and Program state; include the integration manifest for a multi-Goal Program. This composite gate must validate the raw rollout with Canary, transition, handshake, runtime provenance, evidence lifecycle, and completion-telemetry requirements. A declared `model_canary_status`, `model_handshake_status`, model name, or `model_routing_valid` boolean never substitutes for the composite gate. A single-Goal delivery follows the same Program completion gate without an integration manifest.

After the Program controller successfully marks the runtime Program Goal complete, preserve the completion receipt and invoke `$goal-retrospective`. Provide the approved artifacts, all Goal and integration evidence, accepted candidate identity, routing and telemetry records, invalid runs, final acceptance, and the completion receipt. The retrospective is a post-completion audit and cannot substitute for this gate or change the recorded Goal status. If the document cannot be written, report `RETROSPECTIVE_PENDING` with the missing evidence or recovery action.
