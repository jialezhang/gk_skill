---
name: product-to-delivery
description: Use when a user wants to take product intent through approved artifacts and verified delivery, or needs the next valid stage after a pause or restart.
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
2. If product intent is unclear, explicitly invoke the installed `$grill-me` skill. If unavailable, conduct equivalent focused discovery. Do not design implementation yet.
3. When discovery is sufficient, the current main agent invokes `$create-product-prd` directly while running on `gpt-5.6-sol`.
4. Stop after `REVIEW_REQUIRED`. Continue only after explicit approval of the exact PRD revision.
5. Invoke `$assess-goal-scope` before implementation planning. A P80 above 8 hours triggers a split discussion; a P80 above 10 hours triggers a strong recommendation. If the user-input mechanism supports auto-resolution, wait 240 seconds. Silence resolves only Goal packaging to `split_decision: single_goal` with `decision_source: timeout_default_single`.
6. The current main agent invokes `$create-implementation-plan` directly while running on `gpt-5.6-sol` and uses the validated scope decision. A split decision creates one program baseline and 2–3 bounded Goal plans; a single decision creates one Goal plan.
7. Stop after `PLAN_REVIEW_REQUIRED`. Continue only after explicit approval of the exact plan/tasks revisions.
8. Run the Sol/Terra/Luna model-routing Canary before formal execution. Do not start implementation when actual per-turn routing is unverified.
9. Create one runtime Program Goal and `program-state.yaml` before the first Goal starts. Keep it active across every milestone; do not complete or replace it when one Goal reaches `GOAL_TARGET_VERIFIED`.
10. Invoke `$goal-driven-delivery` once per approved Goal. Keep one visible Program task by default; each Goal receives its own worktree, branch, state, checkpoint sequence, and internal model-routed context. Create another visible Codex task only when the required model is unavailable through native subagents, record `VISIBLE_MODEL_CONTEXT_REQUIRED`, and never use a task name as model evidence. One program controller owns the cross-Goal dependency graph, fixed progress denominators, Agent budget, candidate evidence, and coordination-wait accounting.
11. When multiple Goals finish, invoke `$integrate-goals` to merge them in an integration worktree and verify a clean integration commit.
12. Invoke `$review-delivery-gate` for evidence gates, final acceptance, and plan conflicts using the model-routing contract.
13. If a PRD or plan revision invalidates approval, the current main agent returns to and completes the owning stage rather than patching around it or delegating the revision.
14. Before Program completion, run `scripts/validate_completion_gate.py` from the plugin root against the exact routing log, Goal delivery state, candidate evidence, Program state, and optional integration manifest. Do not call the runtime completion tool unless this raw-evidence composite gate passes on the same candidate.

## Main-agent ownership

PRD and implementation-planning work is non-delegable. The current main agent must author, review, revise, and validate every PRD plus every `plan.md`, `tasks.md`, and `verification.md` artifact. Do not spawn, create, or delegate to a child agent, subagent, separate reviewer context, or separate task for this work. Deterministic validators, repository inspection, and documentation tools are allowed because they do not transfer artifact ownership.

The current main agent must be running on `gpt-5.6-sol` for these stages. If that route cannot be verified, return `MAIN_AGENT_SOL_REQUIRED`; do not create a Sol child agent as a workaround.

## Authority

- Product decisions belong to the user.
- PRD authorship/revision and implementation-plan authorship/revision belong only to the current main agent running on Sol. Scope judgment and other high-risk architecture decisions use Sol as routed by their owning stage.
- Runtime scheduling, implementation, debugging, integration, retries, browser acceptance, 阶段真实用户旅程, Provider-boundary acceptance, and final exact-target acceptance belong to Terra.
- Focused tests, typecheck, build, diff checks, baseline comparison, checklist review, and deterministic evidence reconciliation belong to Luna.
- One program controller owns program truth; each Goal controller owns only its Goal state.

Never infer approval from silence, earlier discussion, or a model's confidence.

## Model routing

Use explicit model selection according to the routing surface:

- product discovery, PRD, scope assessment, implementation planning, architecture/plan contradiction, and high-risk security judgment: `gpt-5.6-sol`;
- delivery control, implementation, debugging, local rework, and integration: `gpt-5.6-terra`;
- browser acceptance, 阶段真实用户旅程, runtime lifecycle acceptance, Provider-boundary acceptance, and final exact-target acceptance: `gpt-5.6-terra`;
- focused checks, typecheck, build, diff checks, baseline comparison, checklist review, and deterministic evidence reconciliation: `gpt-5.6-luna`.

For native subagents, select the model at context creation with `fork_turns: "none"` or a positive limited-history value. Full-history forks inherit the parent model and are forbidden for model overrides. When the follow-up API has no model parameter, reuse only the verified context and validate its actual model after every turn. On surfaces that support per-turn selection, pass the model explicitly every turn.

Read actual `turn_context.payload.model` metadata from the runtime rollout after every turn. Append the thread/turn identity, routing surface, model-selection scope, fork mode when applicable, explicit-request fact, requested model, runtime-observed model, observation source, phase, and verification status to `model-routing.jsonl`. Validate the log against the raw rollout rather than trusting its copied `observed_model`. A mismatch returns `MODEL_ROUTE_MISMATCH`, invalidates that turn's output as delivery evidence, and stops dependent work. Never accept an Agent name, `agent_type`, prompt claim, UI label, or self-report as model evidence.

The live Canary requires an initial and an explicit-model follow-up turn for each model, plus the same-thread sequence Terra → Luna → Sol → Terra. Every new execution or acceptance context must then pass a no-write routing handshake before receiving an execution packet. A missing handshake, unknown task class, unavailable rollout turn, or implicit model request blocks formal execution.

Outside PRD and implementation-planning work, use a fresh reviewer context when independence matters. Sol is an escalation path, not the default verifier.

## Recovery

On resume or context compaction, reconstruct current state from approved artifact revisions and `delivery-state.yaml`. Do not trust an earlier narrative summary when it conflicts with durable state or repository evidence. If the delivery predates Program state, apply the legacy-state recovery contract: preserve the former Goal/evidence, create one Program Goal only when unfinished scope remains, and record superseded runtime Goal IDs instead of silently restarting or declaring completion.

For a multi-Goal Program, reconstruct cross-Goal truth from `program-state.yaml` before reading any child Goal state. Validate Program state before completion:

```bash
python3 scripts/validate_program_state.py <program-state.yaml>
```
