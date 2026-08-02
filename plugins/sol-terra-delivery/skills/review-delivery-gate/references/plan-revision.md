# Plan Revision Protocol

The current main agent owns every plan revision. Do not spawn, create, or delegate to a child agent, subagent, separate reviewer context, or separate task for any revision step. Prefer Sol for the planning stage; if unavailable, use the current model and record `sol_route_fallback` without blocking the Goal.

## Revision steps

1. Identify the exact failed assumption/decision and decisive evidence.
2. Determine whether the conflict is technical or product-owned.
3. For a technical conflict, update only affected plan decisions, tasks, dependencies, gates, verification, rollback, and delegation.
4. Increment plan/tasks/verification revisions together.
5. Record rejected alternatives and the new decision rule.
6. Compute affected consumed contracts and mark dependent attempts/gates stale.
7. Require user reapproval when the baseline change is material under the approval protocol; always require it when PRD content changes.

## Prohibited behavior

- Do not rewrite unaffected history.
- Do not let Terra silently wrap reality into the old plan shape.
- Do not preserve approval across material changes without recording why.
- Do not delete failed evidence; mark it superseded by revision.
