# Checkpoint Contract

## When to checkpoint

Checkpoint after each independently runnable vertical slice, approved milestone, or Goal completion. Do not checkpoint half-wired code merely because time passed.

## Required sequence

1. Run the slice's focused checks, relevant type/static checks, and diff check.
2. Inspect protected-data boundaries and confirm no unrelated user changes are staged.
3. Commit only owned files with repository-required decision trailers.
4. Push the Goal branch and verify the remote commit.
5. Record commit SHA, verification evidence, push status, remaining risk, and report time in delivery state.
6. Send a progress report immediately.

Required progress report fields:

- completed outcome and exact target;
- commit SHA and branch;
- implementation completed/total;
- automation completed/total;
- exact-target acceptance completed/total;
- release completed/total;
- current work, P50/P80 remaining estimate, blockers, and next checkpoint.

Final acceptance runs only on a clean committed tree. Dirty-worktree evidence is diagnostic, not release evidence.
