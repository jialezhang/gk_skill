# Codex Native Agent Routing Contract

## Labels are not model configuration

`task_name`, `agent_type`, role names, prompts, and UI labels describe responsibility only. They do
not select or prove a runtime model. Never treat a name containing `terra`, `luna`, or `sol` as
model evidence.

## Native subagent creation

When using Codex native subagents with an explicit model override:

1. Set `model` explicitly at creation.
2. Set `fork_turns` to `"none"` or a positive limited-history value.
3. Never omit `fork_turns` and never use `"all"`: a full-history fork inherits the parent model
   and cannot establish an independent model override.
4. For delegated implementation, omit `agent_type`. A configured role profile can take precedence
   over the explicit spawn model; a label such as `team-executor` is not a safe Terra route.
5. Add `route_class: terra_implementation` and `ROUTING HANDSHAKE ONLY` to the first message. Give
   the first turn no repository-write authority.
6. Inspect the controller rollout and bind the record to the original native `spawn_agent` call.
7. Inspect the child runtime rollout and validate `turn_context.payload.model` before sending an
   execution packet. These two raw records are authoritative. When the bundled route guard runs,
   preserve its matching `SOL_TERRA_ROUTE_VERIFIED nonce=...` marker as supplemental diagnostics;
   a missing marker alone does not invalidate otherwise complete raw native evidence.

For native subagents, `request_explicit: true` means the model was explicitly selected for the
context at creation. Record:

```json
{
  "routing_surface": "native_subagent",
  "model_selection_scope": "context_creation",
  "fork_turns": "none",
  "spawn_controller_thread_id": "...",
  "spawn_call_id": "..."
}
```

The controller and spawn-call identities must resolve to the original `collaboration.spawn_agent`
function call in the controller rollout. Runtime validation reads that call's actual arguments and
requires its `model` and `fork_turns` to match the routing record. A copied or hand-written spawn
configuration is not evidence.

The main agent may still implement directly. These constraints apply when it delegates
implementation, debugging, local rework, or integration to a native subagent. Make up to three
sequential Terra switch attempts for the active execution path. After a verified handshake, reuse
that same Terra context with `followup_task`; do not respawn one context per task. If creation is
denied, raw spawn/rollout evidence is unavailable, or the actual model does not match, discard that
child context before the next attempt. After the third failure, continue in the parent with its
current model. When the optional route guard is active, it permits one pending Terra switch per
parent session at a time and expires abandoned pending state after 60 seconds; ordinary
non-implementation subagents do not consume that pending route.

When the route guard exposes permission inheritance, record both `parent_permission_mode` and
`observed_permission_mode` and require equality. Do not synthesize these fields when the native
runtime does not expose them. A browser/UI permission claim never replaces runtime evidence.

Recommended delegated implementation spawn:

```json
{
  "task_name": "terra_implementation",
  "model": "gpt-5.6-terra",
  "reasoning_effort": "high",
  "fork_turns": "none",
  "message": "route_class: terra_implementation\nROUTING HANDSHAKE ONLY"
}
```

Do not include `agent_type` in this spawn.

If the follow-up API cannot accept a model parameter, reuse only that verified context and inspect
the actual model after every follow-up turn. A changed, missing, or ambiguous runtime model
quarantines the turn. If the API supports per-turn model selection, pass it explicitly every time
and set `model_selection_scope: "turn"`.

## Other routing surfaces

For a Codex task or another surface that accepts per-turn model selection, pass the required model
on every turn and record `routing_surface: "codex_task"` plus
`model_selection_scope: "turn"`. When a Sol stage runs in the main context, record
`routing_surface: "main_agent"` and verify the current runtime turn directly. A Sol stage may also
run in a verified native subagent or Codex task using the corresponding routing surface and model
selection scope. If Sol is unavailable, keep the current model and use the audited
`sol_route_fallback` shape from [model-routing-contract.md](model-routing-contract.md); never claim
that a fallback child uses Sol without matching runtime evidence.

If Terra cannot be selected and verified after three raw attempts, record
`MODEL_ROUTE_UNAVAILABLE` or the more specific route-guard failure and continue the implementation
in the current main context with its existing model. This is a parent-context fallback, not
permission to create a misleadingly named replacement Agent. Final exact-target acceptance may use
the same audited fallback only in a fresh, read-only current-model reviewer context outside every
implementation thread. Browser interactions still run exclusively through Ego Lite.
