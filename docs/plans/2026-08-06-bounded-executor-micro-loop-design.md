# Bounded Executor Micro-loop Design

## Problem

The delivery controller already owns dependency-aware scheduling, evidence, gates, recovery, and
completion. Its task-level rhythm was less explicit: an executor could receive work and return a
handoff, but the contract did not define a small, reviewable unit between ready-queue computation
and a stage checkpoint. Adopting a separate batch controller would create competing state owners
and could add fixed-order execution, routine feedback waits, or premature user escalation.

## Decision

Keep `goal-driven-delivery` as the only Goal controller and add a bounded executor micro-loop inside
its delivery loop. Each execution window contains one to three tasks selected from the current
ready queue. Three is a maximum, not a quota. Selected tasks must have current consumed contracts
and non-overlapping write scopes; coupled work remains one vertical task instead of being split to
fill a window.

For each selected task, the controller records state transitions, supplies a revision-pinned
execution packet, and requires code inspection, the smallest complete implementation, focused
self-checks, diff inspection, and a structured handoff. Existing failure routing remains
authoritative: local defects return to implementation or debugging, plan contradictions escalate
to the planning authority, and product conflicts request a user decision.

Closing a window records one of `continue`, `escalate`, `complete`, or `blocked`. A routine progress
report or checkpoint is not an approval gate. When safe in-scope work remains, the controller
recomputes the ready queue and continues autonomously.

## Persistence and compatibility

Delivery-state schema 1.4 adds an explicit execution policy and an append-only list of execution
windows. The validator fixes the window size at one to three tasks, rejects unsupported next
actions such as `wait_for_feedback`, requires timestamps for completed windows, and permits only
one open window. Older state schemas remain valid because the new keys are required only from 1.4.

## Verification

Behavioral contract tests cover the protocol linkage, bounded autonomous wording, state-template
defaults, rejection of oversized windows, and rejection of feedback-waiting continuation. The
existing toolkit validator remains the full regression gate.
