---
name: integrate-goals
description: Use when two or more approved Goal branches must be combined, verified, and reconciled into one release candidate.
---

# Integrate Goals

Combine only committed Goal outputs. Integration is a Terra implementation task followed by Luna verification; it is not a second planning stage.

Read [references/integration-contract.md](references/integration-contract.md) completely.

## Preconditions

Require every Goal to provide a pushed clean commit, `TARGET_VERIFIED` evidence for its bounded outcome, a valid `model-routing.jsonl`, checkpoint reports, and known deviations. Return `GOAL_INTEGRATION_NOT_READY` if any Goal is missing them.

## Integrate

1. Create a dedicated integration worktree and branch from the approved base commit. Record target repository, base, Goal branches/commits, and merge order.
2. Fetch and verify every remote Goal commit. Merge or cherry-pick in dependency order; never integrate an uncommitted worktree or silently omit a Goal.
3. Route contract-preserving conflicts to the Terra integration owner. Pause and escalate only genuine plan/architecture/product/security contradictions to Sol or the user.
4. Run focused boundary checks after each merge wave. Then run the approved full suite, build/static checks, and exact-target E2E on the integrated tree.
5. Commit the integrated result, verify the worktree is clean, push the integration branch, and record `program-integration.json` from [assets/program-integration-template.json](assets/program-integration-template.json).
6. Run the validator, then invoke `$review-delivery-gate` with Luna for routine final acceptance on the clean integration commit.
7. Aggregate Goal session IDs, commits, checkpoint reports, model-routing records, available token usage by model/stage, verification evidence, and unresolved risks into the program handoff and retrospective. Mark unavailable telemetry explicitly; never invent it.

Validate with:

```bash
python3 scripts/validate_integration_manifest.py <program-integration.json>
```

Program completion requires `TARGET_VERIFIED`, a clean pushed integration commit, and no required Goal or release work remaining.
