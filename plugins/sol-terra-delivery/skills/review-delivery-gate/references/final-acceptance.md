# Final Acceptance

## Required reconciliation

For every blocking PRD requirement and journey, record:

```text
requirement → implementation task → build → exact-target execution → raw evidence → reviewer verdict
```

Confirm:

- the primary journey is reachable through the approved entry;
- expected user-visible behavior and authoritative persisted facts agree;
- exact user/owner, data, flags, configuration, and provider were used;
- automated and integration checks passed on the accepted build;
- safety, authorization, idempotency, migration, rollback, compatibility, and Legacy obligations are reconciled;
- no blocking item is only implemented, enabled, executed, blocked, or implicitly deferred;
- all plan revisions and stale attempts are accounted for;
- remaining risks are truly non-blocking and explicit.
- the accepted worktree is clean and `HEAD` equals the recorded pushed commit;
- every review turn has matching requested/observed model metadata;
- every completed checkpoint has a commit, verified push, and progress report.
- every reused check is valid for the same candidate and every missing/invalidated claim has a current execution scenario;
- final acceptance runs on Terra in a thread outside the implementation-thread set.
- every browser journey and screenshot was produced through Ego Lite `ego-browser` under the browser acceptance contract.

## Wrong-target rule

Legacy, fallback, mock, fixture, test provider, static artifact, adjacent route, or another build cannot satisfy acceptance unless the user explicitly approved it as the target before execution.

## Final verdict

Independent Terra final acceptance returns `TARGET_VERIFIED` only with a compact same-candidate evidence index and zero remaining required work. Consume valid Luna deterministic evidence instead of repeating it. Escalate to the current main planning agent only when acceptance exposes a product, plan, architecture, or high-risk security contradiction; prefer Sol and otherwise use `sol_route_fallback`.
