---
name: merge-push-primary
description: Merge a committed source branch into the repository's primary branch and push the primary branch safely. Use when the user explicitly invokes merge-push-primary or asks to merge the current, feature, or working branch into main, master, or the remote default branch and push it. Do not use for ordinary current-branch commits.
---

# Merge Push Primary

Merge only committed source work into the actual remote default branch. Preserve unrelated local changes.

## Workflow

1. Inspect `git rev-parse --show-toplevel`, `git status --short`, `git branch --show-current`, `git remote -v`, and `refs/remotes/origin/HEAD`.
2. Resolve the source branch and primary branch. Prefer the remote default branch; do not assume `main` when repository evidence says otherwise.
3. Require the intended source work to be committed. If it is not, preserve it and stop; do not invoke `commit-push-lore` automatically. Use that skill only when the user explicitly authorized committing and pushing the source work. Never stash or discard unrelated changes silently.
4. Record the immutable source HEAD as `<recorded-source-head>` and the primary HEAD as both pre-merge tips, then run `git fetch origin`. Switch to the primary branch only when Git can preserve the working tree safely, and update it with `git pull --ff-only origin <primary>`; refresh the recorded primary tip after the fast-forward.
5. Before merging, inventory behavior, contracts, and tests unique to both pre-merge tips with the merge base, commit log, and two-sided diffs. Branch recency, the current checkout, and an easier-to-compile side are not authority.
6. Merge the recorded commit, not the mutable branch name, with `git merge --no-ff --no-commit <recorded-source-head>`, unless the repository or user explicitly requires another merge policy. If there is nothing new, stop without creating an empty commit.
7. Apply the conflict-preservation contract below. Resolve conflicts only within the requested merge scope. Do not absorb unrelated dirty files. Report conflicts that require product or ownership judgment.
8. Compare the resolved candidate with both recorded tips and verify every inventoried behavior and test is preserved or intentionally superseded. Run verification appropriate to the merged result. Passing tests alone are not sufficient because a conflict resolution can remove an implementation and its new or changed tests together. Review `git diff --cached --stat`, `git diff --cached --check`, and `git status --short` before committing.
9. Create the merge commit using the repository's message policy. When no Lore policy exists, use an intent-first message with actual `Tested:` evidence and any known `Not-tested:` gaps. Immediately prove inclusion with `git merge-base --is-ancestor <recorded-source-head> HEAD`; do not push if it fails.
10. Push only the primary branch with `git push origin <primary>`, then fetch it again and prove `<recorded-source-head>` is an ancestor of `origin/<primary>`. Do not push or delete the source branch unless explicitly requested.
11. Confirm the push range, `git rev-parse --short HEAD`, `git status --branch --short`, and primary/upstream divergence. Report the source branch, recorded source HEAD, primary branch, merge commit, remote ancestry proof, verification, and remaining local changes.

## Conflict-Preservation Contract

- Do not resolve a whole conflicted file with `ours` or `theirs`, or treat one parent as authoritative. Resolve from the common ancestor hunk by hunk so additions from both parents remain visible.
- Maintain a Conflict ledger in the merge commit body and final report. For every conflicting behavior, contract, test, and documentation change, record `preserve`, `integrate`, or `intentional removal`, plus the supporting verification. Prefer integration when both parents contain valid additions.
- Never delete or weaken new or changed tests merely to make the merged suite pass. Restore the intended behavior or escalate the genuine contract conflict.
- Intentional removal of code, behavior, or tests requires an explicit user instruction or approved repository requirement that names the removed capability. Record that authority in the Conflict ledger. A clean build, green tests, branch age, verbal urgency, or merge convenience is not deletion authority.
- Preserve all uncommitted and unrelated code. Do not use reset, checkout-overwrite, stash-and-drop, or cleanup commands as conflict-resolution shortcuts.

## Boundaries

- Never force-push, rewrite shared history, or silently choose a different remote or primary branch.
- Do not merge uncommitted source work or represent fallback/legacy verification as acceptance evidence.
- Do not claim a merge complete until the two-tip semantic audit is complete; textual conflict resolution and a green suite are only intermediate evidence.
- If repository identity or the intended remote is ambiguous, stop before pushing and report the exact mismatch.
