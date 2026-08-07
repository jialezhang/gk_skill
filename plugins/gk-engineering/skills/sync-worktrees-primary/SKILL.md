---
name: sync-worktrees-primary
description: Use when a user asks to consolidate every active Git worktree branch into the remote default branch, make primary contain the latest multi-worktree changes, or restart a service after worktree-based development.
---

# Sync Worktrees Primary

Treat the recorded tips of all active worktree branches as a closed integration set. Do not restart the service until every tip is proven reachable from the pushed primary branch and the runtime is proven to use that revision.

## Workflow

1. Inspect `git rev-parse --show-toplevel`, `git remote -v`, `refs/remotes/origin/HEAD`, and `git worktree list --porcelain`.
2. Build the integration inventory. An active source worktree must have an existing directory, a local branch ref, and no `prunable`, `bare`, or `detached` marker. Exclude the primary branch itself. Ignore local or remote branches with no active worktree. Report stale records; do not prune or delete them.
3. In every active worktree, record its path, branch, HEAD, upstream, and `git status --short`. Inspect dirty diffs before deciding ownership.
4. Make every source worktree clean before recording its final source HEAD. Commit only clearly intended paths through `commit-push-lore`. Never use `git add .`, `git add -A`, `git add -u`, stash, reset, or an automatic “commit everything” shortcut. A broad request to “sync everything” is not evidence that an ambiguous dirty change belongs to the delivery; require repository ownership evidence or explicit user/author confirmation. Otherwise stop: the full-sync guarantee is not yet possible.
5. Run `git fetch origin`. If the primary branch is already checked out in another worktree, operate in that worktree. Otherwise switch a clean, safe worktree to the actual remote default branch. Never force a checkout over local changes. Update primary with `git pull --ff-only origin <primary>`.
6. Order source branches by known dependencies. Skip a source only when `git merge-base --is-ancestor <source-head> HEAD` succeeds. Merge each remaining recorded HEAD with `git merge --no-ff --no-commit <source-head>`, review the staged diff and `git diff --cached --check`, run focused checks, then create a repository-compliant Lore merge commit. Resolve only unambiguous in-scope conflicts; stop on product or ownership conflicts.
7. Run the complete verification appropriate to the consolidated primary branch. Prove every recorded source HEAD is an ancestor of local primary. Push only primary with `git push origin <primary>`, fetch again, then prove every source HEAD is an ancestor of `origin/<primary>` and local primary has zero upstream divergence.
8. Discover the authoritative deployment and restart procedure from repository instructions, deployment configuration, and live process/container metadata. If multiple plausible environments or services remain, stop after the verified push and ask which target is live. Do not guess between commands.
9. Update the service through its documented deployment path so it uses the pushed primary revision; do not copy files ad hoc from another worktree. Run the documented restart and health check. Verify a revision endpoint, artifact label, process working tree, container image, or equivalent evidence ties the healthy runtime to the pushed primary HEAD.
10. Report the worktree inventory, excluded records, source HEADs, merge commits, verification, pushed primary HEAD, restart command, health evidence, and any remaining dirty or unintegrated state.

## Completion Contract

Claim completion only when all are true:

- Every active source worktree is clean and its recorded HEAD is reachable from remote primary.
- Consolidated-primary verification passed on the actual pushed revision.
- The intended service restarted successfully and health evidence identifies that revision.

Otherwise report the exact incomplete stage. A successful push without an identified restart target is partial completion, not a successful sync-and-restart.

## Boundaries

- Do not include detached, prunable, deleted, inactive, or merely remote branches.
- Do not prune worktrees, delete branches, force-push, rewrite history, or silently discard changes.
- Do not restart before remote-primary ancestry and verification succeed.
- Do not claim “latest” from branch names, timestamps, or a clean primary worktree alone; prove commit ancestry and runtime revision.
