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
6. quarantine all delegated output after a missing or mismatched route; for implementation,
   debugging, local rework, delivery control, or integration, continue in the current main context
   with its existing model and record an auditable Terra-route fallback; for Sol stages, continue
   on the current model under `sol_route_fallback` when live capability evidence proves Sol
   unavailable.

Read [native-agent-routing.md](native-agent-routing.md) completely before using Codex native
subagents. Native model overrides require `fork_turns: "none"` or a positive limited-history
value. A full-history fork, Agent name, `agent_type`, role, prompt, or UI label is not model
selection.

Required handshake record (route-guard permission and nonce fields may be appended when available):

```json
{"thread_id":"...","turn_id":"handshake-...","task_class":"routing_handshake","routing_surface":"native_subagent","model_selection_scope":"context_creation","fork_turns":"none","spawn_controller_thread_id":"...","spawn_call_id":"...","requested_model":"gpt-5.6-terra","request_explicit":true,"observed_model":"gpt-5.6-terra","observed_source":"rollout.turn_context.payload.model","phase":"handshake","verified":true,"allowed_reason":"routing_canary","write_allowed":false}
```

Required execution record:

```json
{"thread_id":"...","turn_id":"...","handshake_turn_id":"handshake-...","task_class":"implementation","requested_model":"gpt-5.6-terra","request_explicit":true,"observed_model":"gpt-5.6-terra","observed_source":"rollout.turn_context.payload.model","phase":"execution","verified":true,"allowed_reason":"implementation"}
```

Required fallback execution record when the Terra switch fails:

```json
{
  "thread_id": "parent-thread",
  "turn_id": "implementation-fallback-1",
  "task_class": "implementation",
  "routing_surface": "main_agent",
  "model_selection_scope": "current_context",
  "requested_model": "gpt-5.6-sol",
  "request_explicit": true,
  "observed_model": "gpt-5.6-sol",
  "observed_source": "rollout.turn_context.payload.model",
  "phase": "execution",
  "verified": true,
  "write_allowed": true,
  "allowed_reason": "terra_route_fallback",
  "fallback_attempted": true,
  "fallback_from_model": "gpt-5.6-terra",
  "fallback_attempts": [
    {"attempt": 1, "spawn_controller_thread_id": "parent-thread", "spawn_call_id": "spawn-terra-1", "failure_reason": "handshake_not_verified"},
    {"attempt": 2, "spawn_controller_thread_id": "parent-thread", "spawn_call_id": "spawn-terra-2", "failure_reason": "model_mismatch"},
    {"attempt": 3, "spawn_controller_thread_id": "parent-thread", "spawn_call_id": "spawn-terra-3", "failure_reason": "route_unavailable"}
  ]
}
```

The current model in this example is Sol only because the parent was already running Sol; use the
actual previous model. Allowed fallback reasons are `spawn_rejected`, `handshake_not_verified`,
`model_mismatch`, `permission_mismatch`, `route_guard_error`, and `route_unavailable`. The raw
controller rollout must contain all three referenced explicit Terra spawn attempts, numbered
1–3 with distinct call identities. A fallback record with fewer than three valid attempts cannot
replace the handshake.

Required current-model record when Sol is unavailable:

```json
{
  "thread_id": "main-thread",
  "turn_id": "plan-sol-fallback-1",
  "task_class": "implementation_plan",
  "routing_surface": "main_agent",
  "model_selection_scope": "current_context",
  "requested_model": "actual-current-model",
  "request_explicit": false,
  "observed_model": "actual-current-model",
  "observed_source": "rollout.turn_context.payload.model",
  "phase": "execution",
  "verified": true,
  "write_allowed": true,
  "allowed_reason": "sol_route_fallback",
  "fallback_attempted": true,
  "fallback_from_model": "gpt-5.6-sol",
  "fallback_failure_reason": "model_not_listed",
  "fallback_evidence_source": "live_model_capabilities",
  "fallback_evidence": "the active routing surface did not list gpt-5.6-sol"
}
```

Allowed Sol failure reasons are `model_not_listed`, `route_unavailable`, `selection_rejected`, and `runtime_model_mismatch`. Evidence sources are `live_model_capabilities`, `model_selection_error`, or `runtime_turn_context`. The requested and observed fallback model must match the actual current model. `request_explicit` is false because the stage did not independently select the fallback model. This record permits the Goal lifecycle to continue; never label an unevidenced route or fallback child as Sol.

Use the same current-model shape with `allowed_reason: "luna_route_fallback"` and
`fallback_from_model: "gpt-5.6-luna"` when the active routing surface does not expose Luna. Luna
fallback remains limited to deterministic checks, reconciliation, and Canary/transition slots.
Use `allowed_reason: "terra_route_fallback"` only after three raw explicit Terra spawn attempts.
For final acceptance that fallback must execute in a fresh read-only reviewer context outside all
implementation threads and preserve `implementation_thread_ids` plus
`independence_verified: true`.

Validate with:

```bash
python3 scripts/validate_model_routing.py <model-routing.jsonl> \
  --require-handshake \
  --require-runtime-evidence
```

Run the command from the plugin root. The validator locates the rollout by `thread_id`, matches
`turn_id`, and reads every matching `turn_context.payload.model`. For native handshakes it also
locates the original controller `spawn_agent` call by `spawn_controller_thread_id` and
`spawn_call_id`, then verifies the actual `model`, `fork_turns`, and absence of a conflicting
`agent_type`. Permission inheritance and the one-time nonce are optional supplemental evidence
emitted by the bundled route guard when that hook surface is active. Copied routing fields are not
authoritative. Missing, ambiguous, or mismatched raw runtime evidence fails validation; a missing
nonce by itself does not. A rejected record cannot support a gate or completion claim.

## Historical empty-log recovery

An old receipt does not supply missing model-routing intent and never exempts a delivery from the
runtime-evidence gate. When a governed delivery predates durable logging but its routing-event
records and raw rollouts still exist, assemble those records into a recovery JSONL and run from the
plugin root:

```bash
python3 scripts/recover_model_routing.py \
  --log <model-routing.jsonl> \
  --source <model-routing-recovery.jsonl> \
  --completion-ready
```

The command accepts only a missing or whitespace-only destination, validates every recovered turn
against `turn_context.payload.model`, applies the full Canary/transition/handshake requirements,
and replaces the log atomically only after all checks pass. A forged, partial, mismatched, missing,
or ambiguous rollout leaves the destination untouched.

Recovery changes the routing-log digest. Preserve any prior receipt as immutable superseded
history, rerun `validate_completion_gate.py --receipt ...`, and use the newly issued receipt for the
terminal transition. Never edit the prior receipt or claim it became valid after the log changed.
If the semantic routing fields or raw runtime evidence cannot be reconstructed, rerun the missing
route-dependent work or acceptance on the same candidate; do not infer them from an Agent label,
model self-report, or receipt summary.

## Live Canary

Before formal delivery:

1. create one minimal task for each of Sol, Terra, and Luna;
2. run an initial and an explicit-model follow-up turn in each available model task;
3. create one transition task and explicitly run Terra → Luna → Sol → Terra in the same thread;
4. record the real thread/turn identities and runtime metadata;
5. run:

```bash
python3 scripts/validate_model_routing.py <model-routing.jsonl> \
  --require-canary \
  --require-transition-canary \
  --require-runtime-evidence
```

`MODEL_ROUTE_MISMATCH`, `MODEL_HANDSHAKE_REQUIRED`, or
`MODEL_HANDSHAKE_SCOPE_MISMATCH` invalidates the delegated context. For implementation-class work,
discard it and retry sequentially until three attempts have failed, then continue in the current
main context using the fallback record above. Do not retry beyond three. Unknown task classes,
missing runtime evidence, incomplete or forged fallback attempts, and mismatched execution records
still block delivery evidence.

When Sol or Luna is unavailable on the active routing surface, execute its initial/follow-up Canary
turns and corresponding transition slot on the current model. Each substituted turn must carry the
complete role-specific fallback record with `write_allowed: false`. Terra Canary substitution still
requires three raw failed Terra spawn attempts. An absent preferred role model by itself never
blocks the Goal.

Prefer a separate visible Codex task for Luna when that surface exposes the model. Otherwise use
the current context under `luna_route_fallback`. A task named “Luna verifier” is not Luna evidence.

## Role boundaries

- **Sol:** preferred for product discovery, PRD authorship, scope assessment, implementation planning, product decisions, architecture/plan contradictions, and high-risk security judgment. If unavailable, the current model performs the work under `sol_route_fallback`.
- **Terra:** preferred delegated model for implementation, debugging, integration, and
  code-quality review; browser acceptance, 阶段真实用户旅程, runtime/provider-boundary acceptance,
  and final exact-target acceptance retain Terra as the preferred route. When Terra cannot be
  verified after three raw attempts, the current model continues under the audited fallback;
  final acceptance additionally requires a fresh independent read-only reviewer context.
- **Luna:** deterministic low-complexity checks only: focused tests, typecheck, build, diff check, baseline comparison, checklist review, and evidence reconciliation. Luna must not own browser execution, runtime lifecycle judgment, user-experience judgment, or final acceptance.

Final exact-target acceptance must run in a fresh Terra thread, or a fresh audited current-model
Terra-fallback thread, that is not one of the implementation threads. Its record must include
`implementation_thread_ids` and `independence_verified: true`; otherwise the acceptance evidence is
invalid.
