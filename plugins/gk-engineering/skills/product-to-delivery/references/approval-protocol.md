# Approval Protocol

## Valid approval

Approval must identify or unambiguously refer to the current artifact revision and come from the user. Accept natural language such as “批准这版 PRD” or a workflow gate response tied to the revision.

Before recording approval:

1. show the artifact path and revision;
2. summarize material decisions and unresolved non-blocking risks;
3. confirm no blocking review finding remains;
4. update only approval metadata.

## Invalid approval

Do not approve based on:

- silence or continuation;
- a prior revision's approval;
- author/reviewer self-assertion;
- a generic request to “keep going” when several revisions exist;
- approval of an adjacent design or conversation summary.

## Revision invalidation

Material changes to product content reset PRD approval. Material changes to architecture, task scope, dependencies, gates, rollback, or completion reset plan approval. Typographical and non-semantic edits may retain approval but must be recorded as such.
