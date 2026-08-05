#!/usr/bin/env python3
"""Validate the complete delivery gate, including raw runtime model evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_contract import file_digest  # noqa: E402


def run_validator(relative: str, *args: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / relative), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return []
    detail = result.stderr.strip() or result.stdout.strip() or "validator failed"
    return [f"{relative}: {line}" for line in detail.splitlines()]


def load_json(path: Path, label: str, errors: list[str]) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{label}: invalid JSON: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label}: root must be an object")
        return {}
    return value


def load_routing(path: Path, errors: list[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        errors.append(f"routing log: {error}")
        return records
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(f"routing log line {line_number}: invalid JSON: {error.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"routing log line {line_number}: record must be an object")
            continue
        records.append(value)
    return records


def runtime_rollout_paths(
    records: list[dict[str, object]], roots: list[Path]
) -> list[Path]:
    """Collect every raw rollout file consulted by routing validation."""
    thread_ids: set[str] = set()
    for record in records:
        for key in ("thread_id", "spawn_controller_thread_id"):
            value = record.get(key)
            if isinstance(value, str) and value:
                thread_ids.add(value)
        attempts = record.get("fallback_attempts")
        if isinstance(attempts, list):
            for attempt in attempts:
                if not isinstance(attempt, dict):
                    continue
                controller = attempt.get("spawn_controller_thread_id")
                if isinstance(controller, str) and controller:
                    thread_ids.add(controller)
    matches: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for thread_id in thread_ids:
            matches.update(root.rglob(f"*{thread_id}*.jsonl"))
    return sorted(matches)


def yaml_scalar(path: Path, section: str, key: str) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"(?ms)^{re.escape(section)}:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
        text,
    )
    block = match.group(1) if match else ""
    scalar = re.search(
        rf"^\s{{2}}{re.escape(key)}:\s*[\"']?([^\"'\n]*)",
        block,
        re.MULTILINE,
    )
    return scalar.group(1).strip() if scalar else None


def yaml_top_scalar(path: Path, key: str) -> str | None:
    match = re.search(
        rf"^{re.escape(key)}:\s*[\"']?([^\"'\n]*)",
        path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def resolve_state_path(state: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else state.parent / path


def write_atomic_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing-log", type=Path, required=True)
    parser.add_argument("--delivery-state", type=Path, required=True)
    parser.add_argument("--candidate-evidence", type=Path, required=True)
    parser.add_argument("--program-state", type=Path, required=True)
    parser.add_argument("--project-profile", type=Path)
    parser.add_argument("--integration-manifest", type=Path)
    parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument(
        "--archived-root",
        type=Path,
        default=Path.home() / ".codex" / "archived_sessions",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Atomically issue the completion receipt after every gate passes.",
    )
    args = parser.parse_args()

    if args.report is not None and args.receipt is not None:
        parser.error("use only one of --report or --receipt")

    errors: list[str] = []
    required_paths = {
        "routing log": args.routing_log,
        "delivery state": args.delivery_state,
        "candidate evidence": args.candidate_evidence,
        "program state": args.program_state,
    }
    if args.integration_manifest is not None:
        required_paths["integration manifest"] = args.integration_manifest
    profile_path = args.project_profile
    if profile_path is None:
        profile_path = resolve_state_path(
            args.delivery_state,
            yaml_top_scalar(args.delivery_state, "project_profile_path"),
        )
    for label, path in required_paths.items():
        if not path.is_file():
            errors.append(f"{label} not found: {path}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if profile_path is not None:
        if profile_path.is_file():
            required_paths["project profile"] = profile_path
        else:
            errors.append(f"project profile not found: {profile_path}")

    errors.extend(
        run_validator(
            "scripts/validate_model_routing.py",
            str(args.routing_log),
            "--require-canary",
            "--require-transition-canary",
            "--require-handshake",
            "--require-runtime-evidence",
            "--sessions-root",
            str(args.sessions_root),
            "--archived-root",
            str(args.archived_root),
        )
    )
    if profile_path is not None and profile_path.is_file():
        errors.extend(
            run_validator("scripts/validate_project_profile.py", str(profile_path))
        )
    telemetry_path = resolve_state_path(
        args.delivery_state,
        yaml_scalar(args.delivery_state, "completion_telemetry", "snapshot_path"),
    )
    if telemetry_path is None:
        errors.append("delivery state completion telemetry snapshot_path is missing")
    elif not telemetry_path.is_file():
        errors.append(f"completion telemetry snapshot not found: {telemetry_path}")
    else:
        errors.extend(
            run_validator("scripts/validate_completion_telemetry.py", str(telemetry_path))
        )
    errors.extend(
        run_validator(
            "skills/goal-driven-delivery/scripts/validate_delivery_state.py",
            str(args.delivery_state),
        )
    )
    candidate_validator_args = [str(args.candidate_evidence)]
    if profile_path is not None and profile_path.is_file():
        candidate_validator_args.extend(["--project-profile", str(profile_path)])
    errors.extend(
        run_validator(
            "skills/goal-driven-delivery/scripts/validate_candidate_evidence.py",
            *candidate_validator_args,
        )
    )
    errors.extend(
        run_validator(
            "skills/product-to-delivery/scripts/validate_program_state.py",
            str(args.program_state),
        )
    )
    if args.integration_manifest is not None:
        errors.extend(
            run_validator(
                "skills/integrate-goals/scripts/validate_integration_manifest.py",
                str(args.integration_manifest),
            )
        )

    candidate = load_json(args.candidate_evidence, "candidate evidence", errors)
    routing = load_routing(args.routing_log, errors)
    candidate_commit = candidate.get("candidate_commit")
    delivery_commit = yaml_scalar(args.delivery_state, "candidate", "commit")
    program_commit = yaml_scalar(args.program_state, "candidate", "commit")
    if not candidate_commit or candidate_commit != delivery_commit or candidate_commit != program_commit:
        errors.append(
            "COMPLETION_CANDIDATE_MISMATCH "
            f"candidate={candidate_commit!r} delivery={delivery_commit!r} program={program_commit!r}"
        )

    acceptance = candidate.get("final_acceptance")
    if not isinstance(acceptance, dict):
        errors.append("candidate final_acceptance is missing")
        acceptance = {}
    reviewer_thread = acceptance.get("reviewer_thread_id")
    reviewer_turn = acceptance.get("reviewer_turn_id")
    matching_acceptance = [
        record
        for record in routing
        if record.get("task_class") == "final_target_acceptance"
        and record.get("thread_id") == reviewer_thread
        and record.get("turn_id") == reviewer_turn
    ]
    if len(matching_acceptance) != 1:
        errors.append(
            "FINAL_ACCEPTANCE_ROUTING_RECORD_REQUIRED "
            f"thread={reviewer_thread!r} turn={reviewer_turn!r}"
        )
    else:
        acceptance_route = matching_acceptance[0]
        terra_or_fallback = (
            acceptance_route.get("requested_model") == "gpt-5.6-terra"
            or (
                acceptance_route.get("allowed_reason") == "terra_route_fallback"
                and acceptance_route.get("fallback_from_model") == "gpt-5.6-terra"
            )
        )
        if not terra_or_fallback:
            errors.append("TERRA_OR_AUDITED_FALLBACK_FINAL_ACCEPTANCE_REQUIRED")

    implementation_threads = acceptance.get("implementation_thread_ids")
    routed_implementation_threads = {
        str(record.get("thread_id"))
        for record in routing
        if record.get("task_class") in {"implementation", "debugging", "local_rework", "integration"}
        and (
            record.get("requested_model") == "gpt-5.6-terra"
            or record.get("allowed_reason") == "terra_route_fallback"
        )
    }
    if not isinstance(implementation_threads, list) or not implementation_threads:
        errors.append("candidate implementation_thread_ids must be non-empty")
    else:
        missing_threads = sorted(
            str(item)
            for item in implementation_threads
            if str(item) not in routed_implementation_threads
        )
        if missing_threads:
            errors.append(
                f"IMPLEMENTATION_ROUTING_RECORDS_MISSING threads={missing_threads}"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    inputs = dict(required_paths)
    for index, path in enumerate(
        runtime_rollout_paths(routing, [args.sessions_root, args.archived_root]), 1
    ):
        inputs[f"runtime rollout {index:03d}"] = path
    report = {
        "schema_version": "1.0",
        "status": "ready",
        "candidate_commit": candidate_commit,
        "issued_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "inputs": {
            label.replace(" ", "_"): {
                "path": str(path.resolve()),
                "sha256": file_digest(
                    path,
                    "terminal_state"
                    if label in {"delivery state", "program state"}
                    else "raw",
                ),
                "digest_mode": (
                    "terminal_state"
                    if label in {"delivery state", "program state"}
                    else "raw"
                ),
            }
            for label, path in inputs.items()
        },
        "runtime_model_evidence": "validated",
        "final_acceptance_thread_id": reviewer_thread,
        "final_acceptance_turn_id": reviewer_turn,
    }
    output_path = args.receipt or args.report
    if output_path is not None:
        write_atomic_json(output_path, report)
    print(json.dumps(report, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
