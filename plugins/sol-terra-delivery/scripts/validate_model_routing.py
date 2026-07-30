#!/usr/bin/env python3
"""Validate observed per-turn model routing records."""

from __future__ import annotations

import argparse
import json
import re
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
    "terra_route_fallback",
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
    "code_quality_review",
    "browser_acceptance",
    "browser_e2e",
    "stage_user_journey",
    "runtime_lifecycle_acceptance",
    "provider_boundary_acceptance",
    "routine_final_acceptance",
    "final_target_acceptance",
}
TERRA_FALLBACK_TASKS = {
    "delivery_control",
    "implementation",
    "debugging",
    "local_rework",
    "integration",
}
TERRA_FALLBACK_REASONS = {
    "spawn_rejected",
    "handshake_not_verified",
    "model_mismatch",
    "permission_mismatch",
    "route_guard_error",
    "route_unavailable",
}
LUNA_TASKS = {
    "focused_tests",
    "typecheck",
    "build_check",
    "diff_check",
    "baseline_compare",
    "checklist_review",
    "evidence_reconciliation",
    "routine_verification",
}
ROUTING_TASKS = {"routing_canary", "routing_transition", "routing_handshake"}
KNOWN_TASKS = SOL_TASKS | TERRA_TASKS | LUNA_TASKS | ROUTING_TASKS
CANARY_PHASES = {"initial", "followup"}
ROUTING_SURFACES = {"main_agent", "native_subagent", "codex_task"}
MODEL_SELECTION_SCOPES = {"turn", "context_creation", "current_context"}
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


def runtime_spawn_arguments(
    controller_thread_id: str,
    spawn_call_id: str,
    roots: list[Path],
) -> tuple[list[dict[str, object]], list[Path]]:
    matches: list[dict[str, object]] = []
    sources: list[Path] = []
    for path in rollout_files(controller_thread_id, roots):
        matched = False
        for raw in path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "response_item":
                continue
            payload = event.get("payload")
            if (
                not isinstance(payload, dict)
                or payload.get("type") != "function_call"
                or payload.get("namespace") != "collaboration"
                or payload.get("name") != "spawn_agent"
                or payload.get("call_id") != spawn_call_id
            ):
                continue
            arguments = payload.get("arguments")
            if not isinstance(arguments, str):
                continue
            try:
                decoded = json.loads(arguments)
            except json.JSONDecodeError:
                continue
            if isinstance(decoded, dict):
                matches.append(decoded)
                matched = True
        if matched:
            sources.append(path)
    return matches, sources


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routing_log", type=Path)
    parser.add_argument("--require-canary", action="store_true")
    parser.add_argument("--require-transition-canary", action="store_true")
    parser.add_argument("--require-handshake", action="store_true")
    parser.add_argument("--require-permission-inheritance", action="store_true")
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
    valid_handshakes: dict[str, tuple[str, str]] = {}
    valid_fallback_turns: set[str] = set()
    pending_execution_records: list[tuple[int, dict[str, object]]] = []
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
        write_allowed = record.get("write_allowed")
        routing_surface = record.get("routing_surface")
        model_selection_scope = record.get("model_selection_scope")
        fork_turns = record.get("fork_turns")
        spawn_controller_thread_id = record.get("spawn_controller_thread_id")
        spawn_call_id = record.get("spawn_call_id")
        fallback_attempted = record.get("fallback_attempted")
        fallback_from_model = record.get("fallback_from_model")
        fallback_attempts = record.get("fallback_attempts")

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
        fallback_candidate = (
            task_class in TERRA_FALLBACK_TASKS
            and requested != "gpt-5.6-terra"
        )
        fallback_valid = False
        if fallback_candidate:
            fallback_errors: list[str] = []
            if reason != "terra_route_fallback":
                fallback_errors.append("allowed_reason must be terra_route_fallback")
            if routing_surface != "main_agent":
                fallback_errors.append("routing_surface must be main_agent")
            if model_selection_scope != "current_context":
                fallback_errors.append("model_selection_scope must be current_context")
            if write_allowed is not True:
                fallback_errors.append("write_allowed must be true")
            if fallback_attempted is not True:
                fallback_errors.append("fallback_attempted must be true")
            if fallback_from_model != "gpt-5.6-terra":
                fallback_errors.append("fallback_from_model must be gpt-5.6-terra")
            if not isinstance(fallback_attempts, list) or len(fallback_attempts) != 3:
                fallback_errors.append(
                    "TERRA_FALLBACK_REQUIRES_THREE_ATTEMPTS"
                )
            else:
                seen_attempt_calls: set[tuple[str, str]] = set()
                for expected_attempt, attempt in enumerate(fallback_attempts, 1):
                    if not isinstance(attempt, dict):
                        fallback_errors.append(
                            f"attempt {expected_attempt} must be an object"
                        )
                        continue
                    attempt_number = attempt.get("attempt")
                    attempt_controller = attempt.get("spawn_controller_thread_id")
                    attempt_call = attempt.get("spawn_call_id")
                    attempt_reason = attempt.get("failure_reason")
                    if attempt_number != expected_attempt:
                        fallback_errors.append(
                            f"attempt {expected_attempt} has invalid sequence "
                            f"value={attempt_number!r}"
                        )
                    if (
                        not isinstance(attempt_controller, str)
                        or not attempt_controller
                        or not isinstance(attempt_call, str)
                        or not attempt_call
                    ):
                        fallback_errors.append(
                            f"attempt {expected_attempt} spawn identity is required"
                        )
                    else:
                        attempt_identity = (attempt_controller, attempt_call)
                        if attempt_identity in seen_attempt_calls:
                            fallback_errors.append(
                                f"attempt {expected_attempt} reuses spawn identity "
                                f"{attempt_identity!r}"
                            )
                        seen_attempt_calls.add(attempt_identity)
                    if attempt_reason not in TERRA_FALLBACK_REASONS:
                        fallback_errors.append(
                            f"attempt {expected_attempt} has invalid "
                            f"failure_reason={attempt_reason!r}"
                        )
            if fallback_errors:
                errors.append(
                    f"line {line_number}: TERRA_FALLBACK_EVIDENCE_REQUIRED: "
                    + "; ".join(fallback_errors)
                )
            else:
                fallback_valid = True
                if isinstance(turn_id, str) and turn_id:
                    valid_fallback_turns.add(turn_id)
        elif task_class in TERRA_TASKS and requested != "gpt-5.6-terra":
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
        if task_class == "routing_handshake":
            if write_allowed is not False:
                errors.append(f"line {line_number}: HANDSHAKE_MUST_BE_READ_ONLY")
            if phase != "handshake":
                errors.append(f"line {line_number}: HANDSHAKE_PHASE_REQUIRED")
            if routing_surface not in ROUTING_SURFACES:
                errors.append(
                    f"line {line_number}: ROUTING_SURFACE_REQUIRED: {routing_surface!r}"
                )
            if model_selection_scope not in MODEL_SELECTION_SCOPES:
                errors.append(
                    f"line {line_number}: MODEL_SELECTION_SCOPE_REQUIRED: "
                    f"{model_selection_scope!r}"
                )
            native_config_valid = True
            permission_config_valid = True
            if routing_surface == "native_subagent":
                if model_selection_scope != "context_creation":
                    errors.append(
                        f"line {line_number}: NATIVE_MODEL_MUST_BE_SELECTED_AT_CONTEXT_CREATION"
                    )
                    native_config_valid = False
                if fork_turns == "all" or fork_turns is None:
                    errors.append(
                        f"line {line_number}: NATIVE_FULL_HISTORY_MODEL_OVERRIDE_FORBIDDEN"
                    )
                    native_config_valid = False
                elif fork_turns != "none" and not (
                    isinstance(fork_turns, str)
                    and fork_turns.isdigit()
                    and int(fork_turns) > 0
                ):
                    errors.append(
                        f"line {line_number}: INVALID_NATIVE_FORK_TURNS: {fork_turns!r}"
                    )
                    native_config_valid = False
                if args.require_permission_inheritance:
                    parent_permission_mode = record.get("parent_permission_mode")
                    observed_permission_mode = record.get("observed_permission_mode")
                    permission_source = record.get("permission_source")
                    route_guard_nonce = record.get("route_guard_nonce")
                    if not isinstance(parent_permission_mode, str) or not parent_permission_mode:
                        errors.append(
                            f"line {line_number}: PARENT_PERMISSION_MODE_REQUIRED"
                        )
                        permission_config_valid = False
                    if observed_permission_mode != parent_permission_mode:
                        errors.append(
                            f"line {line_number}: PERMISSION_INHERITANCE_MISMATCH "
                            f"parent={parent_permission_mode!r} observed={observed_permission_mode!r}"
                        )
                        permission_config_valid = False
                    if record.get("permission_inherited") is not True:
                        errors.append(
                            f"line {line_number}: PERMISSION_INHERITANCE_UNVERIFIED"
                        )
                        permission_config_valid = False
                    if permission_source != "hook.SubagentStart.permission_mode":
                        errors.append(
                            f"line {line_number}: INVALID_PERMISSION_SOURCE: "
                            f"{permission_source!r}"
                        )
                        permission_config_valid = False
                    if not isinstance(route_guard_nonce, str) or not re.fullmatch(
                        r"[0-9a-f]{24}", route_guard_nonce
                    ):
                        errors.append(
                            f"line {line_number}: ROUTE_GUARD_NONCE_REQUIRED"
                        )
                        permission_config_valid = False
            if (
                isinstance(turn_id, str)
                and isinstance(thread_id, str)
                and isinstance(requested, str)
                and requested == observed
                and verified is True
                and routing_surface in ROUTING_SURFACES
                and model_selection_scope in MODEL_SELECTION_SCOPES
                and native_config_valid
                and permission_config_valid
            ):
                valid_handshakes[turn_id] = (thread_id, requested)
        elif task_class in SOL_TASKS | TERRA_TASKS | LUNA_TASKS:
            pending_execution_records.append((line_number, record))

        if task_class == "final_target_acceptance":
            implementation_threads = record.get("implementation_thread_ids")
            independence_verified = record.get("independence_verified")
            if (
                not isinstance(implementation_threads, list)
                or not implementation_threads
                or not all(isinstance(item, str) and item for item in implementation_threads)
            ):
                errors.append(
                    f"line {line_number}: FINAL_ACCEPTANCE_IMPLEMENTATION_THREADS_REQUIRED"
                )
            elif thread_id in implementation_threads:
                errors.append(f"line {line_number}: FINAL_ACCEPTANCE_NOT_INDEPENDENT")
            if independence_verified is not True:
                errors.append(f"line {line_number}: FINAL_ACCEPTANCE_INDEPENDENCE_UNVERIFIED")

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
            if task_class == "routing_handshake" and routing_surface == "native_subagent":
                if (
                    not isinstance(spawn_controller_thread_id, str)
                    or not spawn_controller_thread_id
                    or not isinstance(spawn_call_id, str)
                    or not spawn_call_id
                ):
                    errors.append(
                        f"line {line_number}: NATIVE_SPAWN_RUNTIME_IDENTITY_REQUIRED"
                    )
                else:
                    spawn_arguments, spawn_sources = runtime_spawn_arguments(
                        spawn_controller_thread_id,
                        spawn_call_id,
                        roots,
                    )
                    if not spawn_arguments:
                        errors.append(
                            f"line {line_number}: NATIVE_SPAWN_CALL_NOT_FOUND "
                            f"controller={spawn_controller_thread_id!r} call={spawn_call_id!r}"
                        )
                    elif len(spawn_arguments) != 1:
                        errors.append(
                            f"line {line_number}: NATIVE_SPAWN_CALL_AMBIGUOUS "
                            f"matches={len(spawn_arguments)}"
                        )
                    else:
                        runtime_spawn = spawn_arguments[0]
                        runtime_source_count += len(spawn_sources)
                        if runtime_spawn.get("model") != requested:
                            errors.append(
                                f"line {line_number}: NATIVE_SPAWN_MODEL_MISMATCH "
                                f"requested={requested!r} runtime={runtime_spawn.get('model')!r}"
                            )
                        if runtime_spawn.get("fork_turns") != fork_turns:
                            errors.append(
                                f"line {line_number}: NATIVE_SPAWN_FORK_MISMATCH "
                                f"logged={fork_turns!r} runtime={runtime_spawn.get('fork_turns')!r}"
                            )
                        if runtime_spawn.get("agent_type"):
                            errors.append(
                                f"line {line_number}: NATIVE_SPAWN_AGENT_TYPE_FORBIDDEN "
                                f"runtime={runtime_spawn.get('agent_type')!r}"
                            )
            if fallback_valid:
                assert isinstance(fallback_attempts, list)
                for attempt in fallback_attempts:
                    assert isinstance(attempt, dict)
                    attempt_number = attempt["attempt"]
                    attempt_controller = str(attempt["spawn_controller_thread_id"])
                    attempt_call = str(attempt["spawn_call_id"])
                    fallback_spawns, fallback_sources = runtime_spawn_arguments(
                        attempt_controller,
                        attempt_call,
                        roots,
                    )
                    if not fallback_spawns:
                        errors.append(
                            f"line {line_number}: TERRA_FALLBACK_SPAWN_NOT_FOUND "
                            f"attempt={attempt_number} controller={attempt_controller!r} "
                            f"call={attempt_call!r}"
                        )
                    elif len(fallback_spawns) != 1:
                        errors.append(
                            f"line {line_number}: TERRA_FALLBACK_SPAWN_AMBIGUOUS "
                            f"attempt={attempt_number} matches={len(fallback_spawns)}"
                        )
                    else:
                        runtime_source_count += len(fallback_sources)
                        if fallback_spawns[0].get("model") != "gpt-5.6-terra":
                            errors.append(
                                f"line {line_number}: "
                                "TERRA_FALLBACK_ATTEMPT_MODEL_MISMATCH "
                                f"attempt={attempt_number} "
                                f"runtime={fallback_spawns[0].get('model')!r}"
                            )

    if args.require_handshake:
        for line_number, record in pending_execution_records:
            if record.get("turn_id") in valid_fallback_turns:
                continue
            handshake_turn_id = record.get("handshake_turn_id")
            if not isinstance(handshake_turn_id, str) or not handshake_turn_id:
                errors.append(f"line {line_number}: MODEL_HANDSHAKE_REQUIRED")
                continue
            handshake = valid_handshakes.get(handshake_turn_id)
            if handshake is None:
                errors.append(
                    f"line {line_number}: MODEL_HANDSHAKE_NOT_VERIFIED: {handshake_turn_id!r}"
                )
                continue
            handshake_scope = (record.get("thread_id"), record.get("requested_model"))
            if handshake != handshake_scope:
                errors.append(
                    f"line {line_number}: MODEL_HANDSHAKE_SCOPE_MISMATCH "
                    f"handshake={handshake!r} execution={handshake_scope!r}"
                )

    if not seen_turns:
        errors.append("routing log contains no turns")
    if args.require_canary:
        expected_canary_phases = {
            (model, phase) for model in MODELS for phase in CANARY_PHASES
        }
        missing_canary_phases = sorted(expected_canary_phases - canary_phases)
        if missing_canary_phases:
            errors.append(
                f"MODEL_CANARY_INCOMPLETE missing={missing_canary_phases}"
            )
    if args.require_transition_canary:
        actual_indexes = sorted(transitions)
        transition_models = [transitions[index][1] for index in actual_indexes]
        actual_threads = {thread for thread, _model in transitions.values()}
        if (
            actual_indexes != [1, 2, 3, 4]
            or transition_models != TRANSITION_MODELS
            or len(actual_threads) != 1
        ):
            errors.append(
                "MODEL_TRANSITION_CANARY_INCOMPLETE "
                f"indexes={actual_indexes} models={transition_models} "
                f"threads={sorted(actual_threads)}"
            )

    if errors:
        for issue in errors:
            print(f"ERROR: {issue}", file=sys.stderr)
        return 1
    runtime_note = f", {runtime_source_count} runtime evidence matches" if args.require_runtime_evidence else ""
    print(f"OK: {args.routing_log} ({len(seen_turns)} turns{runtime_note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
