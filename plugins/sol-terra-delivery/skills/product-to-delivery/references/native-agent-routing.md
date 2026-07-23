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
4. Give the first turn no repository-write authority. It is the routing handshake only.
5. Inspect the runtime rollout and validate `turn_context.payload.model` before sending an
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

If the follow-up API cannot accept a model parameter, reuse only that verified context and inspect
the actual model after every follow-up turn. A changed, missing, or ambiguous runtime model
quarantines the turn. If the API supports per-turn model selection, pass it explicitly every time
and set `model_selection_scope: "turn"`.

## Other routing surfaces

For a Codex task or another surface that accepts per-turn model selection, pass the required model
on every turn and record `routing_surface: "codex_task"` plus
`model_selection_scope: "turn"`. For main-agent-only Sol stages, record
`routing_surface: "main_agent"` and verify the current runtime turn directly.

If the required model cannot be selected and verified on the available surface, return
`MODEL_ROUTE_UNAVAILABLE`. Do not fall back to another model, create a misleadingly named Agent, or
continue implementation as diagnostic work.
