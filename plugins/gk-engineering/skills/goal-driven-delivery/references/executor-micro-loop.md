# Bounded Executor Micro-loop

This loop is the task-level execution rhythm inside the Goal controller. It does not replace the
ready queue, delivery state machine, gates, checkpoint contract, or completion transaction.

## Open an execution window

1. Reconcile the current Goal state and compute the ready queue from dependencies and gates.
2. Select 1–3 tasks whose consumed contracts are current and which have non-overlapping write scopes.
   One coupled vertical task is better than several artificially split tasks.
3. Record the execution window ID, selected task IDs, start time, and expected outcome in
   `delivery-state.yaml` before assignment.
4. Issue one revision-pinned execution packet per selected task. Selection never follows prose
   ordering merely to fill the window, and three tasks is a maximum rather than a quota.

## Execute each task

For every task in the window:

1. mark it `assigned`, then `in_progress`, through the controller;
2. inspect the actual code and current diff before editing;
3. implement the smallest complete outcome that preserves approved contracts;
4. run the focused self-checks required by the impact map;
5. inspect the owned diff and protected-resource boundaries;
6. return the structured handoff with raw verification output, deviations, and remaining risk;
7. let the controller route the result and update task, attempt, evidence, and gate state.

Executors may adjust reversible local mechanics. A local failure returns to the same executor or
debugger with a changed hypothesis. A plan contradiction becomes a Sol escalation packet. A
product-level conflict is the point at which affected work stops for a user decision.

## Close and continue

Close the window when every selected task has reached a routed outcome, or when a genuine blocker
prevents further safe work. Record the close time and exactly one next action:

- `continue` — recompute the ready queue and open the next bounded window;
- `escalate` — pause affected work while the planning authority resolves a contract conflict;
- `complete` — no implementation work remains and the Goal proceeds to its remaining gates;
- `blocked` — an external or product blocker satisfies the blocking policy.

If the window completes an independently runnable vertical slice or planned stage, run the
checkpoint contract and report its evidence. Do not wait for routine human feedback after a window
or checkpoint when safe in-scope work remains. A progress report is an observation boundary, not
an approval gate. User input is required only where the approval, product, authority, destructive
action, or external-effect contracts explicitly require it.
