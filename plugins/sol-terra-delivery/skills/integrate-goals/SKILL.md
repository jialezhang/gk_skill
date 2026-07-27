---
name: integrate-goals
description: Use when two or more approved Goal branches must be combined, verified, and reconciled into one release candidate.
---

# Integrate Goals

Combine only committed Goal outputs. Integration is a Terra implementation task, Luna deterministic checking, and independent Terra final acceptance; it is not a second planning stage.

Read [references/integration-contract.md](references/integration-contract.md) completely.
Read [../product-to-delivery/references/native-agent-routing.md](../product-to-delivery/references/native-agent-routing.md) completely.

## Preconditions

Require every Goal to provide a pushed clean commit, `TARGET_VERIFIED` evidence for its bounded outcome, accepted evidence-lifecycle records, a runtime-validated `model-routing.jsonl`, a pre-terminal completion telemetry snapshot, checkpoint reports, and known deviations. Before integration work, create or reuse a Terra context that has passed a no-write handshake with valid native routing configuration. Return `GOAL_INTEGRATION_NOT_READY` if any Goal or route is missing them.

## Integrate

1. Create a dedicated integration worktree and branch from the approved base commit. Record target repository, base, Goal branches/commits, and merge order.
2. Fetch and verify every remote Goal commit. Merge or cherry-pick in dependency order; never integrate an uncommitted worktree or silently omit a Goal.
3. Route contract-preserving conflicts to the Terra integration owner. Pause and escalate only genuine plan/architecture/product/security contradictions to Sol or the user.
4. Run focused boundary checks after each merge wave. Reconcile valid evidence and explicitly invalidate evidence whose candidate, consumed artifact, or runtime provenance no longer applies. Then run the approved full suite/build once on the frozen integrated candidate and only the exact-target scenarios whose claims remain uncovered or invalidated. Re-capture runtime provenance on the integrated target; a Goal branch process or build is never evidence for the integration branch.
5. Commit the integrated result, verify the worktree is clean, push the integration branch, and record `program-integration.json` from [assets/program-integration-template.json](assets/program-integration-template.json).
6. Run the validator, then invoke `$review-delivery-gate` with an independent Terra acceptance context on the clean integration commit. The integration implementer and final acceptance reviewer must have different thread IDs.
7. Aggregate Goal session IDs, commits, checkpoint reports, model-routing records, exact-turn token usage by model/stage, verification evidence, and unresolved risks into the program handoff and retrospective. Generate telemetry with `python3 scripts/collect_delivery_telemetry.py <model-routing.jsonl> --completion-snapshot --output <snapshot>` before the Program terminal transition; merge per-Goal snapshots without replaying forked parent turns. Mark unavailable telemetry explicitly; never invent it.

Validate with:

```bash
python3 scripts/validate_integration_manifest.py <program-integration.json>
```

Program completion requires independent Terra `TARGET_VERIFIED`, a clean pushed integration commit, no required Goal or release work remaining for the declared completion scope, and a passing `scripts/validate_completion_gate.py` run that includes this integration manifest and raw runtime model evidence. Goal-level verification or declared routing booleans never complete the Program.
