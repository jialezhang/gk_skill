---
name: merge-push-primary
description: Merge a committed source branch into the repository's primary branch and push the primary branch safely. Use when the user explicitly invokes merge-push-primary or asks to merge the current, feature, or working branch into main, master, or the remote default branch and push it. Do not use for ordinary current-branch commits.
---

# Merge Push Primary

Merge only committed source work into the actual remote default branch. Preserve unrelated local changes.

## Workflow

1. Inspect `git rev-parse --show-toplevel`, `git status --short`, `git branch --show-current`, `git remote -v`, and `refs/remotes/origin/HEAD`.
2. Resolve the source branch and primary branch. Prefer the remote default branch; do not assume `main` when repository evidence says otherwise.
3. Require the intended source work to be committed. If it is not, complete it with `commit-push-lore` first. Never stash or discard unrelated changes silently.
4. Record the source HEAD, then run `git fetch origin`. Switch to the primary branch only when Git can preserve the working tree safely, and update it with `git pull --ff-only origin <primary>`.
5. Merge with `git merge --no-ff --no-commit <source>`, unless the repository or user explicitly requires another merge policy. If there is nothing new, stop without creating an empty commit.
6. Resolve conflicts only within the requested merge scope. Do not absorb unrelated dirty files. Report conflicts that require product or ownership judgment.
7. Run verification appropriate to the merged result. Review `git diff --cached --stat`, `git diff --cached --check`, and `git status --short` before committing.
8. Create the merge commit using the repository's message policy. When no Lore policy exists, use an intent-first message with actual `Tested:` evidence and any known `Not-tested:` gaps.
9. Push only the primary branch with `git push origin <primary>`. Do not push or delete the source branch unless explicitly requested.
10. Confirm the push range, `git rev-parse --short HEAD`, `git status --branch --short`, and primary/upstream divergence. Report the source branch, primary branch, merge commit, remote, verification, and remaining local changes.

## Boundaries

- Never force-push, rewrite shared history, or silently choose a different remote or primary branch.
- Do not merge uncommitted source work or represent fallback/legacy verification as acceptance evidence.
- If repository identity or the intended remote is ambiguous, stop before pushing and report the exact mismatch.
