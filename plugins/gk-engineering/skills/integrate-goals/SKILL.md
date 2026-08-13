---
name: integrate-goals
description: Use when two or more approved Goal branches must be combined, verified, and reconciled into one release candidate.
---

# Integrate Goals

Combine only committed Goal outputs. Prefer Terra for integration, Luna for deterministic checking,
and Terra for independent final acceptance. Use the corresponding audited current-model fallback
when a preferred route is unavailable; it is not a second planning stage.

Read [references/integration-contract.md](references/integration-contract.md) completely.
Read [../product-to-delivery/references/native-agent-routing.md](../product-to-delivery/references/native-agent-routing.md) completely.

**REQUIRED SUB-SKILL:** Read and apply the conflict-preservation rules from `merge-push-primary` before merging or cherry-picking any Goal commit.

## Preconditions

Require every Goal to provide a pushed clean commit, `TARGET_VERIFIED` evidence for its bounded outcome, accepted evidence-lifecycle records, a runtime-validated `model-routing.jsonl`, a pre-terminal completion telemetry snapshot, checkpoint reports, and known deviations. Before integration work, create or reuse a Terra context that has passed a no-write handshake with valid native routing configuration. Return `GOAL_INTEGRATION_NOT_READY` if any Goal or route is missing them.

## Integrate

1. Create a dedicated integration worktree and branch from the approved base commit. Record target repository, base, Goal branches/commits, and merge order.
2. Fetch and verify every remote Goal commit. Merge or cherry-pick in dependency order; never integrate an uncommitted worktree or silently omit a Goal. Apply the conflict-preservation rules from `merge-push-primary` to every merge or cherry-pick: inventory both tips, forbid whole-file side selection, preserve or integrate each Goal's new behavior and tests, compare the candidate against both inputs, and require an explicit user instruction or approved repository requirement for removals.
3. Route contract-preserving conflicts to the Terra integration owner. Pause and escalate only genuine plan/architecture/product/security contradictions to the current main planning agent or the user. Prefer Sol; if unavailable, use the current model under `sol_route_fallback`.
4. Run focused boundary checks after each merge wave. Reconcile valid evidence and explicitly invalidate evidence whose candidate, consumed artifact, or runtime provenance no longer applies. Then run the approved full suite/build once on the frozen integrated candidate and only the exact-target scenarios whose claims remain uncovered or invalidated. Re-capture runtime provenance on the integrated target; a Goal branch process or build is never evidence for the integration branch.
5. Commit the integrated result, verify the worktree is clean, push the integration branch, and record `program-integration.json` from [assets/program-integration-template.json](assets/program-integration-template.json).
6. Run the validator, then invoke `$review-delivery-gate` with an independent Terra or audited
   Terra-fallback acceptance context on the clean integration commit. The integration implementer
   and final acceptance reviewer must have different thread IDs.
7. Aggregate Goal session IDs, commits, checkpoint reports, model-routing records, exact-turn token usage by model/stage, verification evidence, invalid runs, and unresolved risks into the Program completion handoff consumed by `$goal-retrospective`. Generate telemetry with `python3 scripts/collect_delivery_telemetry.py <model-routing.jsonl> --completion-snapshot --output <snapshot>` before the Program terminal transition; merge per-Goal snapshots without replaying forked parent turns. Mark unavailable telemetry explicitly; never invent it. The Program controller invokes the retrospective only after capturing the runtime completion receipt.

Validate with:

```bash
python3 scripts/validate_integration_manifest.py <program-integration.json>
```

Program completion requires independent Terra or audited Terra-fallback `TARGET_VERIFIED`, a clean
pushed integration commit, no required Goal or release work remaining for the declared completion
scope, and a passing `scripts/validate_completion_gate.py` run that includes this integration
manifest and raw runtime model evidence. Goal-level verification or declared routing booleans never
complete the Program.
