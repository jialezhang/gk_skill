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
{"turn_id":"...","task_class":"implementation","requested_model":"gpt-5.6-terra","observed_model":"gpt-5.6-terra","verified":true,"allowed_reason":"implementation"}
```

Validate with:

```bash
python3 scripts/validate_model_routing.py <model-routing.jsonl>
```

Run the command from the plugin root. A record rejected by the validator cannot support a gate or completion claim.

## Live Canary

Before formal delivery, create one minimal turn and one follow-up turn for each of Sol, Terra, and Luna. Record observed metadata, then run:

```bash
python3 scripts/validate_model_routing.py <model-routing.jsonl> --require-canary
```

`MODEL_ROUTE_MISMATCH`, missing metadata, or an incomplete Canary blocks delivery. Reinstall/configure the plugin or repair routing before spending implementation tokens.

## Allowed Sol use

Sol is allowed for product discovery, PRD authorship, scope assessment, implementation planning, product decisions, architecture/plan contradictions, and high-risk security judgment. Routine verification, final checklist reconciliation, and uncomplicated exact-target acceptance use Luna. Terra owns execution and integration.
