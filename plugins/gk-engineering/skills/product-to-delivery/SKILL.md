---
name: product-to-delivery
description: Use when a user wants to route product or technical work through the appropriate level of planning and verified delivery, including deciding whether a PRD is needed or resuming an existing governed lifecycle.
---

# Product to Delivery

Act as the lifecycle controller, not as a second delivery runtime.

Read these references completely before routing a stage:

- [references/lifecycle-contract.md](references/lifecycle-contract.md)
- [references/stage-routing.md](references/stage-routing.md)
- [references/approval-protocol.md](references/approval-protocol.md)
- [references/model-routing-contract.md](references/model-routing-contract.md)
- [references/native-agent-routing.md](references/native-agent-routing.md)

## Route the current stage

1. Inspect existing artifacts before deciding the stage. Never restart discovery merely because the task changed agent or session.
2. Classify whether the request changes product outcomes or only the technical means. Product behavior, user flows, P0/P1 scope, public contracts, safety/compliance rules, data ownership, release scope, or significant cost belongs to the governed PRD lane. A bug fix, refactor, dependency/configuration change, migration, or internal implementation change may use the technical-change lane when acceptance is clear and product boundaries remain unchanged.
3. When no approved PRD exists and the request can remain a technical change, ask whether a PRD is needed before creating one. State a recommendation and one-sentence rationale. Silence does not choose a lane and must not be treated as approval or `PRD_NOT_REQUIRED`.
4. If the user chooses `PRD_NOT_REQUIRED`, record the decision, bounded technical objective, constraints, and acceptance checks in the current task context. Continue through the technical-change lane with proportionate planning, implementation, tests, and verification. Do not manufacture PRD, scope, Goal, or governed completion artifacts.
5. If the user chooses `PRD_REQUIRED`, or the request crosses a governed product boundary, invoke `$grill-me` when intent is unclear; otherwise the current main agent invokes `$create-product-prd` directly. Prefer `gpt-5.6-sol`; when the live routing surface does not expose Sol or rejects the selection, keep the current model and record `sol_route_fallback` instead of blocking the lifecycle.
6. Stop after `REVIEW_REQUIRED`. Continue only after explicit approval of the exact PRD revision.
7. Invoke `$assess-goal-scope` before governed implementation planning. A P80 above 8 hours triggers a split discussion; a P80 above 10 hours triggers a strong recommendation. If the user-input mechanism supports auto-resolution, wait 240 seconds. Silence resolves only Goal packaging to `split_decision: single_goal` with `decision_source: timeout_default_single`.
8. The current main agent invokes `$create-implementation-plan` directly, preferring `gpt-5.6-sol` and otherwise continuing on the current model under `sol_route_fallback`, and uses the validated scope decision. A split decision creates one program baseline and 2–3 bounded Goal plans; a single decision creates one Goal plan.
9. Stop after `PLAN_REVIEW_REQUIRED`. Continue only after explicit approval of the exact plan/tasks revisions.
10. Run the Sol/Terra/Luna model-routing Canary before formal governed execution. A live, evidenced `sol_route_fallback` satisfies the Sol slots when Sol is unavailable; do not block Goal delivery solely because Sol is absent. Other unverified or mismatched routes still block their dependent evidence.
11. Create one runtime Program Goal and `program-state.yaml` before the first governed Goal starts. Keep it active across every milestone; do not complete or replace it when one Goal reaches `GOAL_TARGET_VERIFIED`.
12. Invoke `$goal-driven-delivery` once per approved Goal. Keep one visible Program task by default; each Goal receives its own worktree, branch, state, checkpoint sequence, and internal model-routed context. Create another visible Codex task only when the required model is unavailable through native subagents, record `VISIBLE_MODEL_CONTEXT_REQUIRED`, and never use a task name as model evidence. One program controller owns the cross-Goal dependency graph, fixed progress denominators, Agent budget, candidate evidence, and coordination-wait accounting.
13. When multiple Goals finish, invoke `$integrate-goals` to merge them in an integration worktree and verify a clean integration commit.
14. Invoke `$review-delivery-gate` for governed evidence gates, final acceptance, and plan conflicts using the model-routing contract.
15. If a PRD or plan revision invalidates approval, the current main agent returns to and completes the owning stage rather than patching around it or delegating the revision.
16. Before governed Program completion, run `scripts/validate_completion_gate.py` from the plugin root against the exact routing log, Goal delivery state, candidate evidence, Program state, and optional integration manifest. Do not call the runtime completion tool unless this raw-evidence composite gate passes on the same candidate.
17. After the runtime Program Goal is marked complete, preserve the completion receipt with its Goal/thread identity, final status, `tokensUsed`, `timeUsedSeconds`, and timestamps. Invoke `$goal-retrospective` with that receipt plus the approved artifacts, delivery state, candidate evidence, Git/build/release identity, routing log, telemetry, and final acceptance evidence.
18. Treat the retrospective as a required post-completion audit, never as acceptance evidence or a substitute for the completion gate. For a multi-Goal Program, generate one Program-level retrospective that accounts for every child Goal and invalid run. If evidence is unavailable, record it as unsampled or unverified; do not invent values or reverse an already valid completion. Report a failed document write as `RETROSPECTIVE_PENDING` with the exact recovery action.

## Main-agent ownership

PRD and implementation-planning work is non-delegable. The current main agent must author, review, revise, and validate every PRD plus every `plan.md`, `tasks.md`, and `verification.md` artifact. Do not spawn, create, or delegate to a child agent, subagent, separate reviewer context, or separate task for this work. Deterministic validators, repository inspection, and documentation tools are allowed because they do not transfer artifact ownership.

Prefer `gpt-5.6-sol` for these stages. If Sol is not listed by the live routing surface, selection is rejected, or runtime metadata proves a mismatch, continue in the same main-agent context with the current model. Append an audited `sol_route_fallback` record with the failure reason and live evidence; never return `MAIN_AGENT_SOL_REQUIRED`, spawn a misleading Sol child, or block a Goal solely because Sol is unavailable.

## Authority

- Product decisions belong to the user.
- PRD authorship/revision and implementation-plan authorship/revision belong only to the current main agent. Prefer Sol; if unavailable, the current model retains ownership under `sol_route_fallback`. Scope judgment and other high-risk architecture decisions follow the same rule.
- Runtime scheduling, implementation, debugging, integration, and retries belong to Terra. Browser acceptance, 阶段真实用户旅程, and browser portions of Provider/final acceptance use Terra judgment while every browser interaction runs exclusively through Ego Lite `ego-browser`.
- Focused tests, typecheck, build, diff checks, baseline comparison, checklist review, and deterministic evidence reconciliation belong to Luna.
- One program controller owns program truth; each Goal controller owns only its Goal state.

Never infer approval from silence, earlier discussion, or a model's confidence.

## Model routing

Use explicit model selection according to the routing surface:

- product discovery, PRD, scope assessment, implementation planning, architecture/plan contradiction, and high-risk security judgment: prefer `gpt-5.6-sol`; if unavailable, keep the current model and record `sol_route_fallback` with live capability or selection-failure evidence;
- delivery control, implementation, debugging, local rework, and integration: prefer
  `gpt-5.6-terra`; if three sequential delegated switch attempts fail, the current main agent
  continues directly with its existing model and records all attempts in `terra_route_fallback`;
- browser acceptance, 阶段真实用户旅程, runtime lifecycle acceptance, Provider-boundary acceptance, and final exact-target acceptance: `gpt-5.6-terra`; all browser operations and browser evidence must use Ego Lite `ego-browser`;
- focused checks, typecheck, build, diff checks, baseline comparison, checklist review, and deterministic evidence reconciliation: `gpt-5.6-luna`.

For native subagents, select the model at context creation with `fork_turns: "none"` or a positive limited-history value. Full-history forks inherit the parent model and are forbidden for model overrides. When the follow-up API has no model parameter, reuse only the verified context and validate its actual model after every turn. On surfaces that support per-turn selection, pass the model explicitly every turn.

Read actual `turn_context.payload.model` metadata from the runtime rollout after every turn. Append the thread/turn identity, routing surface, model-selection scope, fork mode when applicable, explicit-request fact, requested model, runtime-observed model, observation source, phase, and verification status to `model-routing.jsonl`. Validate the log against the raw rollout rather than trusting its copied `observed_model`. A mismatch returns `MODEL_ROUTE_MISMATCH`, invalidates that turn's output as delivery evidence, and stops dependent work. Never accept an Agent name, `agent_type`, prompt claim, UI label, or self-report as model evidence.

The live Canary requires an initial and follow-up turn for each available required model, plus the same-thread sequence Terra → Luna → Sol → Terra. When Sol is unavailable, its two Canary turns and transition slot execute on the current model and carry valid `sol_route_fallback` evidence. Every new delegated execution or acceptance context starts with a no-write routing handshake. For implementation-class work, discard each failed Terra context and try again sequentially, up to three total attempts. After the third failure, return execution to the current main agent/model under the auditable fallback contract; never create parallel handshakes or an unbounded retry loop. Unknown task classes, unavailable rollout evidence for the model that actually executed work, and implicit, incomplete, or forged routing records still block acceptance evidence.

Outside PRD and implementation-planning work, use a fresh reviewer context when independence matters. Sol is an escalation path, not the default verifier.

## Recovery

On resume or context compaction, reconstruct current state from approved artifact revisions and `delivery-state.yaml`. Do not trust an earlier narrative summary when it conflicts with durable state or repository evidence. If the delivery predates Program state, apply the legacy-state recovery contract: preserve the former Goal/evidence, create one Program Goal only when unfinished scope remains, and record superseded runtime Goal IDs instead of silently restarting or declaring completion.

For a multi-Goal Program, reconstruct cross-Goal truth from `program-state.yaml` before reading any child Goal state. Validate Program state before completion:

```bash
python3 scripts/validate_program_state.py <program-state.yaml>
```
