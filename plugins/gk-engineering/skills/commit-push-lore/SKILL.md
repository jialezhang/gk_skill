---
name: commit-push-lore
description: Use when the user explicitly invokes commit-push-lore, requests a Lore-format commit, asks to commit and push the current branch, or a commit hook requires decision-record trailers. Do not use it to merge into the primary branch; use merge-push-primary for that workflow.
---

# Commit Push Lore

Commit only the intended work and push the current branch by default. Preserve unrelated dirty files and remain on the current branch.

## Workflow

1. Inspect `git rev-parse --show-toplevel`, `git status --short`, `git branch --show-current`, the upstream, and `git remote -v`.
2. Identify the requested file scope. Split only obviously independent file groups; leave unrelated changes unstaged.
3. Reuse verification already run for the exact changes, or run the smallest meaningful check when none exists.
4. Stage explicit paths. Never use `git add .` or `git add -A` in a dirty tree.
5. Review `git diff --cached --stat`, `git diff --cached --check`, and `git status --short`. Commit only when the staged scope is correct.
6. Follow the repository's commit-message policy. If it has no Lore policy, use:

```text
<intent line explaining why>

<brief rationale>

Tested: <verification actually run>
Not-tested: <known gap, when applicable>
```

Add `Constraint:`, `Rejected:`, `Confidence:`, `Scope-risk:`, `Reversibility:`, or `Directive:` only when they preserve useful decisions. If a hook rejects the message, treat its output as authoritative and retry only the message.

7. Treat explicit invocation of `commit-push-lore` as authorization to push, even when the user adds no wording about push. Push the current branch with `git push` when it has an upstream, otherwise use `git push -u origin HEAD`. Skip push only when the user explicitly requests commit-only or no-push; do not infer commit-only from silence.
8. Confirm with `git rev-parse --short HEAD` and `git status --branch --short`. Report commit hashes, pushed branch and remote, verification, and remaining unrelated changes.

## Boundaries

- Do not switch branches, merge branches, force-push, stash, discard, or stage unrelated work.
- Do not claim a clean tree when unrelated changes remain.
- If the user asks to merge into the primary branch, hand off to `merge-push-primary` after the source work is committed.
