# Model Routing Contract

## No-write handshake and per-turn enforcement

Thread names and agent roles do not prove model identity. The controller must:

1. create a no-write handshake turn with the explicit required model before assigning work;
2. inspect `rollout.turn_context.payload.model` for that handshake;
3. permit work only when requested and observed models match;
4. on surfaces with per-turn model selection, pass the explicit model on every execution and
   follow-up turn; on native subagents without that parameter, reuse only the explicitly created,
   verified context and validate every runtime turn;
5. append immutable handshake and execution records to `model-routing.jsonl`;
6. quarantine all output after a missing or mismatched route until the work is rerun on the required model.

Read [native-agent-routing.md](native-agent-routing.md) completely before using Codex native
subagents. Native model overrides require `fork_turns: "none"` or a positive limited-history
value. A full-history fork, Agent name, `agent_type`, role, prompt, or UI label is not model
selection.

Required handshake record:

```json
{"thread_id":"...","turn_id":"handshake-...","task_class":"routing_handshake","routing_surface":"native_subagent","model_selection_scope":"context_creation","fork_turns":"none","spawn_controller_thread_id":"...","spawn_call_id":"...","requested_model":"gpt-5.6-terra","request_explicit":true,"observed_model":"gpt-5.6-terra","observed_source":"rollout.turn_context.payload.model","phase":"handshake","verified":true,"allowed_reason":"routing_canary","write_allowed":false}
```

Required execution record:

```json
{"thread_id":"...","turn_id":"...","handshake_turn_id":"handshake-...","task_class":"implementation","requested_model":"gpt-5.6-terra","request_explicit":true,"observed_model":"gpt-5.6-terra","observed_source":"rollout.turn_context.payload.model","phase":"execution","verified":true,"allowed_reason":"implementation"}
```

Validate with:

```bash
python3 scripts/validate_model_routing.py <model-routing.jsonl> \
  --require-handshake \
  --require-runtime-evidence
```

Run the command from the plugin root. The validator locates the rollout by `thread_id`, matches `turn_id`, and reads every matching `turn_context.payload.model`. For native handshakes it also locates the original controller `spawn_agent` call by `spawn_controller_thread_id` and `spawn_call_id`, then verifies the actual `model` and `fork_turns` arguments. Copied routing fields are not authoritative. Missing, ambiguous, or mismatched runtime evidence fails validation. A rejected record cannot support a gate or completion claim.

## Live Canary

Before formal delivery:

1. create one minimal task for each of Sol, Terra, and Luna;
2. run an initial and an explicit-model follow-up turn in each task;
3. create one transition task and explicitly run Terra → Luna → Sol → Terra in the same thread;
4. record the real thread/turn identities and runtime metadata;
5. run:

```bash
python3 scripts/validate_model_routing.py <model-routing.jsonl> \
  --require-canary \
  --require-transition-canary \
  --require-runtime-evidence
```

`MODEL_ROUTE_MISMATCH`, `MODEL_HANDSHAKE_REQUIRED`, `MODEL_HANDSHAKE_SCOPE_MISMATCH`, `RUNTIME_MODEL_MISMATCH`, an implicit follow-up model, unknown task class, missing metadata, or an incomplete Canary blocks delivery. Reinstall/configure the plugin or repair routing before spending implementation tokens.

Use a separate visible Codex task for Luna when the native subagent surface does not expose a Luna model override. A task named “Luna verifier” is not Luna evidence.

## Role boundaries

- **Sol:** product discovery, PRD authorship, scope assessment, implementation planning, product decisions, architecture/plan contradictions, and high-risk security judgment.
- **Terra:** implementation, debugging, integration, code-quality review, browser acceptance, 阶段真实用户旅程, runtime/provider-boundary acceptance, and final exact-target acceptance.
- **Luna:** deterministic low-complexity checks only: focused tests, typecheck, build, diff check, baseline comparison, checklist review, and evidence reconciliation. Luna must not own browser execution, runtime lifecycle judgment, user-experience judgment, or final acceptance.

PRD and implementation-planning use is restricted further: the current main agent must perform all authorship, review, validation, and revision while running on Sol. A controller must not satisfy this route by creating a Sol child agent, subagent, separate reviewer context, or separate task.

Final exact-target acceptance must run in a fresh Terra thread that is not one of the implementation threads. Its record must include `implementation_thread_ids` and `independence_verified: true`; otherwise the acceptance evidence is invalid.
