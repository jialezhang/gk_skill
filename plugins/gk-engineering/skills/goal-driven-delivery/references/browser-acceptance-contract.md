# Ego Lite Browser Acceptance Contract

## Exclusive browser surface

Ego Lite is the exclusive browser surface. Every browser-related acceptance activity must run through the Ego Lite `ego-browser` skill and CLI. This includes opening or navigating pages, clicking, typing, uploading, scrolling, inspecting rendered state, exercising user journeys, collecting screenshots, and closing the browser context.

Do not use Playwright, Chrome control, generic computer-use, built-in browser tools, WebDriver, curl-rendered HTML, or a human's unaudited manual observation as browser acceptance evidence. Non-browser HTTP or CLI probes may supplement diagnostics, but they cannot replace the required Ego Lite journey.

## Required execution shape

1. Create or reuse one isolated Ego Lite task space for the Goal with `useOrCreateTaskSpace`.
2. Pin the candidate commit/build, exact URL, user/owner, flags, data, Provider mode, and expected journey before interaction.
3. Operate the page with `ego-browser nodejs` helpers. Prefer `snapshotText()` and stable locators for semantic pages; use `captureScreenshot()` plus coordinate/keyboard actions for canvas or virtualized surfaces.
4. After every material action, re-observe page state with `snapshotText()`, `pageInfo()`, a screenshot, or an authoritative readback. Do not infer success from a click completing.
5. Record task-space ID, exact URL, action sequence, before/after observations, screenshot or raw-output paths, visible outcome, persisted outcome when applicable, runtime provenance, and failure details in the candidate evidence index.
6. Run browser acceptance from an independent Terra acceptance context when the owning gate requires Terra independence. Ego Lite is the interaction surface; Terra remains responsible for the acceptance judgment.
7. After a prior round confirms the journey is complete, close the task space in a dedicated final Ego Lite invocation with `completeTaskSpace(nameOrId, { keep: false })`, unless user intervention requires an explicit handoff.

## Evidence validity

Browser evidence is valid only when it is bound to the same candidate and exact target as the gate, identifies Ego Lite `ego-browser` as the interaction runner, and contains enough observations to replay the user journey. Evidence from another browser surface is diagnostic and must be rerun through Ego Lite before it can support `GATE_PASSED` or `TARGET_VERIFIED`.
