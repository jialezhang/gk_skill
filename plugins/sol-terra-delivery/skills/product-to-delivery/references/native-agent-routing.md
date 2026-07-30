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
6. Require the bundled route guard to return the matching `SOL_TERRA_ROUTE_VERIFIED nonce=...`
   marker. It validates the actual `SubagentStart.model` and that the subagent inherited the
   parent's creation-time `permission_mode`.
7. Inspect the runtime rollout and validate `turn_context.payload.model` before sending an
   execution packet.

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
denied, the verification marker is absent, or the actual model/permission does not match, discard
that child context before the next attempt. After the third failure, continue in the parent with
its current model. The route guard permits one pending Terra switch per parent session at a time
and expires abandoned pending state after 60 seconds; ordinary non-implementation subagents do not
consume that pending route.

Subagents inherit the parent permission mode at context creation. Record both
`parent_permission_mode` and `observed_permission_mode` in the handshake record and require equality.
When the user changes the parent permission mode, discard the old implementation subagent and
create a new handshake context. A browser/UI claim that Full access is selected does not replace
the observed hook value for the spawned context.

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
`model_selection_scope: "turn"`. For main-agent-only Sol stages, record
`routing_surface: "main_agent"` and verify the current runtime turn directly.

If Terra cannot be selected and verified for delegated implementation, record
`MODEL_ROUTE_UNAVAILABLE` or the more specific route-guard failure and continue the implementation
in the current main context with its existing model. This is a parent-context fallback, not
permission to create a misleadingly named replacement Agent. Browser/runtime acceptance and final
exact-target acceptance retain their own model and independence requirements.
