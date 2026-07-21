#!/usr/bin/env python3
"""Validate observed per-turn model routing records."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


MODELS = {
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
}
SOL_REASONS = {
    "routing_canary",
    "product_discovery",
    "prd_authoring",
    "scope_assessment",
    "implementation_plan",
    "plan_conflict",
    "architecture_conflict",
    "security_high_risk",
    "product_decision",
}
SOL_TASKS = {
    "product_discovery",
    "prd_authoring",
    "scope_assessment",
    "implementation_plan",
    "plan_conflict",
    "architecture_conflict",
    "security_high_risk",
    "product_decision",
}
TERRA_TASKS = {
    "delivery_control",
    "implementation",
    "debugging",
    "local_rework",
    "integration",
}
LUNA_TASKS = {
    "focused_tests",
    "build_check",
    "checklist_review",
    "browser_e2e",
    "routine_verification",
    "routine_final_acceptance",
}
ROUTING_TASKS = {"routing_canary", "routing_transition"}
KNOWN_TASKS = SOL_TASKS | TERRA_TASKS | LUNA_TASKS | ROUTING_TASKS
CANARY_PHASES = {"initial", "followup"}
TRANSITION_MODELS = [
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
]


def rollout_files(thread_id: str, roots: list[Path]) -> list[Path]:
    matches: list[Path] = []
    for root in roots:
        if root.is_dir():
            matches.extend(root.rglob(f"*{thread_id}*.jsonl"))
    return sorted(set(matches))


def runtime_models(thread_id: str, turn_id: str, roots: list[Path]) -> tuple[set[str], list[Path]]:
    models: set[str] = set()
    sources: list[Path] = []
    for path in rollout_files(thread_id, roots):
        matched = False
        for raw in path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "turn_context":
                continue
            payload = event.get("payload")
            if not isinstance(payload, dict) or payload.get("turn_id") != turn_id:
                continue
            model = payload.get("model")
            if isinstance(model, str):
                models.add(model)
                matched = True
        if matched:
            sources.append(path)
    return models, sources


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routing_log", type=Path)
    parser.add_argument("--require-canary", action="store_true")
    parser.add_argument("--require-transition-canary", action="store_true")
    parser.add_argument("--require-runtime-evidence", action="store_true")
    parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument(
        "--archived-root",
        type=Path,
        default=Path.home() / ".codex" / "archived_sessions",
    )
    args = parser.parse_args()

    if not args.routing_log.is_file():
        print(f"ERROR: routing log not found: {args.routing_log}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_turns: set[str] = set()
    canary_phases: set[tuple[str, str]] = set()
    transitions: dict[int, tuple[str, str]] = {}
    runtime_source_count = 0
    roots = [args.sessions_root, args.archived_root]
    for line_number, raw in enumerate(args.routing_log.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(f"line {line_number}: invalid JSON: {error.msg}")
            continue

        thread_id = record.get("thread_id")
        turn_id = record.get("turn_id")
        task_class = record.get("task_class")
        requested = record.get("requested_model")
        request_explicit = record.get("request_explicit")
        observed = record.get("observed_model")
        observed_source = record.get("observed_source")
        phase = record.get("phase")
        verified = record.get("verified")
        reason = record.get("allowed_reason")

        if not isinstance(thread_id, str) or not thread_id:
            errors.append(f"line {line_number}: missing thread_id")

        if not isinstance(turn_id, str) or not turn_id:
            errors.append(f"line {line_number}: missing turn_id")
        elif turn_id in seen_turns:
            errors.append(f"line {line_number}: duplicate turn_id: {turn_id}")
        else:
            seen_turns.add(turn_id)

        if requested not in MODELS or observed not in MODELS:
            errors.append(f"line {line_number}: unsupported requested/observed model")
        if request_explicit is not True:
            errors.append(f"line {line_number}: MODEL_REQUEST_NOT_EXPLICIT")
        if observed_source != "rollout.turn_context.payload.model":
            errors.append(f"line {line_number}: INVALID_OBSERVED_SOURCE: {observed_source!r}")
        if not isinstance(phase, str) or not phase:
            errors.append(f"line {line_number}: missing phase")
        if verified is not True:
            errors.append(f"line {line_number}: MODEL_ROUTE_UNVERIFIED")
        if requested != observed:
            errors.append(
                f"line {line_number}: MODEL_ROUTE_MISMATCH requested={requested!r} observed={observed!r}"
            )

        if task_class not in KNOWN_TASKS:
            errors.append(f"line {line_number}: UNKNOWN_TASK_CLASS: {task_class!r}")
        if requested == "gpt-5.6-sol" and reason not in SOL_REASONS:
            errors.append(f"line {line_number}: SOL_REASON_NOT_ALLOWED: {reason!r}")
        if task_class in SOL_TASKS and requested != "gpt-5.6-sol":
            errors.append(f"line {line_number}: {task_class} must request gpt-5.6-sol")
        if task_class in TERRA_TASKS and requested != "gpt-5.6-terra":
            errors.append(f"line {line_number}: {task_class} must request gpt-5.6-terra")
        if task_class in LUNA_TASKS and requested != "gpt-5.6-luna":
            errors.append(f"line {line_number}: {task_class} must request gpt-5.6-luna")
        if task_class == "routing_canary" and phase in CANARY_PHASES:
            if requested in MODELS and requested == observed and verified is True:
                canary_phases.add((requested, phase))
        if task_class == "routing_transition":
            sequence_index = record.get("sequence_index")
            if not isinstance(sequence_index, int):
                errors.append(f"line {line_number}: transition missing integer sequence_index")
            elif sequence_index in transitions:
                errors.append(f"line {line_number}: duplicate transition sequence_index: {sequence_index}")
            elif isinstance(thread_id, str) and isinstance(requested, str):
                transitions[sequence_index] = (thread_id, requested)

        if args.require_runtime_evidence and isinstance(thread_id, str) and isinstance(turn_id, str):
            actual_models, source_files = runtime_models(thread_id, turn_id, roots)
            if not actual_models:
                errors.append(
                    f"line {line_number}: RUNTIME_TURN_NOT_FOUND thread={thread_id!r} turn={turn_id!r}"
                )
            elif len(actual_models) != 1:
                errors.append(
                    f"line {line_number}: RUNTIME_MODEL_AMBIGUOUS models={sorted(actual_models)}"
                )
            else:
                actual = next(iter(actual_models))
                runtime_source_count += len(source_files)
                if actual != observed or actual != requested:
                    errors.append(
                        f"line {line_number}: RUNTIME_MODEL_MISMATCH "
                        f"requested={requested!r} logged={observed!r} runtime={actual!r}"
                    )

    if not seen_turns:
        errors.append("routing log contains no turns")
    if args.require_canary:
        expected = {(model, phase) for model in MODELS for phase in CANARY_PHASES}
        missing = sorted(expected - canary_phases)
        if missing:
            errors.append(f"MODEL_CANARY_INCOMPLETE missing={missing}")
    if args.require_transition_canary:
        actual_indexes = sorted(transitions)
        actual_models = [transitions[index][1] for index in actual_indexes]
        actual_threads = {thread for thread, _model in transitions.values()}
        if actual_indexes != [1, 2, 3, 4] or actual_models != TRANSITION_MODELS or len(actual_threads) != 1:
            errors.append(
                "MODEL_TRANSITION_CANARY_INCOMPLETE "
                f"indexes={actual_indexes} models={actual_models} threads={sorted(actual_threads)}"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    runtime_note = f", {runtime_source_count} runtime evidence matches" if args.require_runtime_evidence else ""
    print(f"OK: {args.routing_log} ({len(seen_turns)} turns{runtime_note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
