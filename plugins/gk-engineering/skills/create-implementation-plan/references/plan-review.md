# Independent Plan Review

## Review dimensions

### Product coverage

- Every approved requirement and blocking journey maps to tasks and evidence.
- No task changes product scope or silently implements an open product choice.

### Direction and ownership

- Rewrites and new state owners have proven justification.
- Each responsibility and authoritative fact has one owner during each rollout state.
- Legacy handoff and deletion/downgrade conditions are explicit.

### Technical credibility

- Verified facts, assumptions, and recommendations are distinguishable.
- External API claims cite current official evidence or remain `VERIFY_FIRST`.
- The first 阶段真实用户旅程 can falsify the risky direction early.

### Execution fitness

- Dependencies form an executable DAG.
- Tasks define bounded ownership and safe parallelism.
- Terra can execute without recreating architecture decisions.
- Every Goal has bounded P80, worktree/session/branch ownership, checkpoints, and an integration path.
- The current main agent performs routine coverage review and records the result in the planning handoff.
- Plan-level contradictions return to the current main agent's planning pass without spawning a reviewer agent. Prefer Sol; if unavailable, continue on the current model under `sol_route_fallback`.

### Estimate integrity

- Program P50/P80/P90 are wall-clock critical-path percentiles; cumulative Agent workload and expected wait are separate.
- Repository measurements and comparable actuals take precedence over generic human/manual estimates.
- Materialized readiness is not charged again; known missing readiness is base work; partial or unknown readiness has conditional branches and a G-00 re-estimate.
- Mutually exclusive branches are not summed, and common-cause risks have one correlation group and one allowance.
- Program P80 is not obtained by summing every task P80, every Goal P80, or overlapping retry/integration/contingency buffers.
- Every estimate revision preserves the prior baseline, evidence, reason, and split-threshold impact.

### Verification integrity

- Task checks, boundary tests, real-target cases, and gates are distinct.
- Wrong-target, fallback, fixture, mock, and Legacy evidence cannot satisfy target acceptance.
- Completion uses the approved target and artifact revisions.

### Runtime lifecycle integrity

- Interaction, command, business-work, persistence, and presentation terminal states are not conflated.
- Each long-running operation has one authoritative status owner and stable correlation/order keys.
- Subscription lifetime follows the business operation, and event loss or reconnect converges through an authoritative snapshot.
- Duplicate, delayed, out-of-order, and superseded events cannot regress state or repeat side effects.
- All user-visible surfaces share a measurable convergence bound and exact-target interruption evidence.

## Finding ownership

- Product ambiguity → PRD/user.
- Architecture/readiness contradiction → readiness/baseline.
- Missing work or dependency → tasks.
- Missing evidence or gate → verification.
- Local naming/detail preference → non-blocking recommendation.

The plan may enter `PLAN_REVIEW_REQUIRED` only when blocking and major plan-owned findings are resolved.
