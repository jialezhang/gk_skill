# Model Routing Contract

## Per-turn enforcement

Thread names and agent roles do not prove model identity. The controller must:

1. pass the explicit model when creating a task;
2. pass the explicit model again on every follow-up turn;
3. inspect the runtime's observed turn model metadata;
4. append one immutable record to `model-routing.jsonl`;
5. fail closed on missing or mismatched metadata.

Required record:

```json
{"thread_id":"...","turn_id":"...","task_class":"implementation","requested_model":"gpt-5.6-terra","request_explicit":true,"observed_model":"gpt-5.6-terra","observed_source":"rollout.turn_context.payload.model","phase":"execution","verified":true,"allowed_reason":"implementation"}
```

Validate with:

```bash
python3 scripts/validate_model_routing.py <model-routing.jsonl> --require-runtime-evidence
```

Run the command from the plugin root. The validator locates the rollout by `thread_id`, matches `turn_id`, and reads every matching `turn_context.payload.model`. The copied `observed_model` is not authoritative. Missing, ambiguous, or mismatched runtime evidence fails validation. A rejected record cannot support a gate or completion claim.

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

`MODEL_ROUTE_MISMATCH`, `RUNTIME_MODEL_MISMATCH`, an implicit follow-up model, unknown task class, missing metadata, or an incomplete Canary blocks delivery. Reinstall/configure the plugin or repair routing before spending implementation tokens.

Use a separate visible Codex task for Luna when the native subagent surface does not expose a Luna model override. A task named “Luna verifier” is not Luna evidence.

## Allowed Sol use

Sol is allowed for product discovery, PRD authorship, scope assessment, implementation planning, product decisions, architecture/plan contradictions, and high-risk security judgment. Routine verification, final checklist reconciliation, and uncomplicated exact-target acceptance use Luna. Terra owns execution and integration.
