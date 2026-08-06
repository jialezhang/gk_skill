# Checkpoint Contract

## When to checkpoint

Checkpoint after each independently runnable vertical slice, approved milestone, or Goal completion. Do not checkpoint half-wired code merely because time passed.

## Required sequence

1. Run the slice's `fast` checks plus only the `change` checks required by the current impact map. Do not run `full` regression or rebuild merely because a checkpoint exists.
2. Inspect protected-data boundaries and confirm no unrelated user changes are staged.
3. Commit only owned files with repository-required decision trailers.
4. Push the Goal branch and verify the remote commit.
5. Record commit SHA, verification evidence, push status, remaining risk, report time, and every new/continued/invalidated evidence record in delivery state.
6. Send a progress report immediately.

The report does not create an implicit approval gate. Unless an explicit approval, product,
authority, destructive-action, external-effect, or genuine blocker rule applies, close the current
execution window with `next_action: continue` and resume from the ready queue.

Required progress report fields:

- completed outcome and exact target;
- commit SHA and branch;
- implementation completed/total;
- automation completed/total;
- exact-target acceptance completed/total;
- release completed/total;
- accepted, invalidated, and superseded evidence IDs plus affected gates;
- current work, P50/P80 remaining estimate, blockers, and next checkpoint.

Final acceptance runs only on a clean committed tree. Dirty-worktree evidence is diagnostic, not release evidence.

## Progress continuity

Persist progress after every task/gate transition and at least every 15 minutes while work is active. Report user-visible progress at checkpoints and at least every 30 minutes during long stages. Progress must use the four fixed denominators from delivery state; do not hide progress by replacing totals with a narrative status.

## Evidence reuse

Record every check in `test-evidence-index.json`. A reviewer or later stage consumes valid same-candidate evidence and runs only uncovered or invalidated checks. A new reviewer, retry, or model switch does not by itself justify repeating a full suite or build.

At the terminal checkpoint, collect the completion telemetry snapshot before the Goal state transition. State the source and unavailable fields instead of estimating missing model or subagent usage after the fact.
