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

## Wrong-target rule

Legacy, fallback, mock, fixture, test provider, static artifact, adjacent route, or another build cannot satisfy acceptance unless the user explicitly approved it as the target before execution.

## Final verdict

Return `TARGET_VERIFIED` only with a compact evidence index and zero remaining required work. Otherwise return the owning failure state and next action.
