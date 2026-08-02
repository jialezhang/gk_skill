# Execution Packets and Role Briefs

## Packet contents

Every executor receives:

1. task and attempt IDs;
2. exact PRD/plan/tasks revisions;
3. task outcome, dependencies, and acceptance;
4. relevant MUST/FORBIDDEN and consumed contract IDs;
5. bounded write scope and shared-file warnings;
6. verified repository evidence and candidate touchpoints;
7. focused/integration verification commands or discovery instructions;
8. rollback/disable expectations;
9. allowed local deviations and Sol escalation triggers;
10. required handoff schema.
11. explicit requested model, allowed reason, and observed-model recording destination;
12. worktree, branch, port/browser context, checkpoint, and cumulative Agent budget allocation.
13. no-write handshake turn ID and required task-class/model route;
14. baseline evidence, current impact map, `test_level`, Provider mode/cost limit, invalidation keys, and candidate identity;
15. acceptance claims proved by the assigned execution scenario and its evidence destination.
16. for delegated implementation: route-guard nonce, parent and observed permission modes, and the
    exact `SOL_TERRA_ROUTE_VERIFIED` handshake marker.
17. after three failed Terra switches: the ordered three-item spawn-attempt list, each normalized
    failure reason, current main model, and the `terra_route_fallback` routing record destination.
    Do not send the packet to a failed child; after attempt three, the main agent consumes it
    directly.

Do not load unrelated future tasks or the whole acceptance runbook into an executor's active context.

## Common role briefs

### Frontend executor

Own UI, client state, accessibility, visual behavior, and focused frontend tests within assigned scope. Do not redefine server contracts or create a second authoritative state owner.

### Backend executor

Own APIs, services, authorization, domain events, persistence access, and focused backend tests within assigned scope. Do not invent product behavior or weaken owner/safety rules.

### Data executor

Own schema/data migrations, backfills, integrity checks, compatibility, backups, and rollback. Stop before destructive or irreversible operations lacking explicit approval.

### Integration executor

Own contract wiring and end-to-end boundary repair after component contracts are stable. Do not conceal incompatible contracts with an unapproved second state layer.

### Test/verifier

Independently execute required checks and collect raw evidence. Do not rewrite acceptance criteria to match implementation or fix code silently.

## Handoff rejection

Reject a handoff that reports only “done”, substitutes a different target, omits failed checks, lacks diff ownership, changes unapproved contracts, or cannot identify the artifact revision it implemented.
