#!/usr/bin/env python3
"""Validate Program/Goal lifecycle, fixed progress denominators, and completion scope."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_contract import (  # noqa: E402
    COMPLETION_SCOPES,
    GOAL_TERMINAL_STATUSES,
    PROGRAM_STATUSES,
    PROGRAM_VERIFIED_STATUSES,
    version_at_least,
)


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "program_id",
    "status",
    "completion_scope",
    "runtime_goal",
    "superseded_runtime_goals",
    "controller",
    "goals",
    "progress",
    "release",
    "candidate",
    "coordination",
    "created_at",
    "updated_at",
}
def scalar(text: str, key: str, indent: int = 0) -> str | None:
    match = re.search(
        rf"^\s{{{indent}}}{re.escape(key)}:\s*[\"']?([^\"'\n]*)",
        text,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def section(text: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^{re.escape(name)}:\s*(?:\n|$)(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
        text,
    )
    return match.group(1) if match else ""


def bool_value(text: str, key: str, indent: int = 2) -> bool | None:
    value = scalar(text, key, indent)
    if value == "true":
        return True
    if value == "false":
        return False
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    if not args.state.is_file():
        print(f"ERROR: program state not found: {args.state}", file=sys.stderr)
        return 1
    text = args.state.read_text(encoding="utf-8")
    errors: list[str] = []
    top_level = set(re.findall(r"^([a-zA-Z0-9_]+):", text, re.MULTILINE))
    schema_version = scalar(text, "schema_version")
    required_top_level = set(REQUIRED_TOP_LEVEL)
    if version_at_least(schema_version, (1, 2)):
        required_top_level.add("completion_receipt")
    for key in sorted(required_top_level - top_level):
        errors.append(f"missing top-level key: {key}")

    status = scalar(text, "status")
    scope = scalar(text, "completion_scope")
    if status not in PROGRAM_STATUSES:
        errors.append(f"invalid program status: {status!r}")
    if scope not in COMPLETION_SCOPES:
        errors.append(f"invalid completion_scope: {scope!r}")
    if not args.allow_empty and not scalar(text, "program_id"):
        errors.append("missing program_id")

    runtime_goal = section(text, "runtime_goal")
    runtime_created = bool_value(runtime_goal, "created")
    runtime_status = scalar(runtime_goal, "status", 2)
    if status not in {None, "BLOCKED"} and runtime_created is not True and not args.allow_empty:
        errors.append("PROGRAM_RUNTIME_GOAL_NOT_CREATED")
    if status == "COMPLETE" and runtime_status != "complete":
        errors.append("complete Program requires runtime_goal.status: complete")

    progress = section(text, "progress")
    for lane in ("implementation", "automation", "exact_target", "release"):
        completed_raw = scalar(progress, f"{lane}_completed", 2)
        total_raw = scalar(progress, f"{lane}_total", 2)
        if completed_raw is None or total_raw is None:
            errors.append(f"missing progress denominator: {lane}")
            continue
        try:
            completed, total = int(completed_raw), int(total_raw)
        except ValueError:
            errors.append(f"invalid progress denominator: {lane}")
            continue
        if completed < 0 or total < 0 or completed > total:
            errors.append(f"invalid progress values: {lane}={completed}/{total}")
        if status in PROGRAM_VERIFIED_STATUSES and completed != total:
            errors.append(f"terminal Program has incomplete progress: {lane}={completed}/{total}")
    for key in ("current_activity", "last_progress_at"):
        if not scalar(progress, key, 2) and not args.allow_empty:
            errors.append(f"missing progress.{key}")

    goals = section(text, "goals")
    goal_ids = re.findall(r"^\s{2}- goal_id:\s*[\"']?([^\"'\n]+)", goals, re.MULTILINE)
    goal_statuses = re.findall(r"^\s{4}status:\s*([A-Z_]+)\s*$", goals, re.MULTILINE)
    if not goal_ids and not args.allow_empty:
        errors.append("Program must contain at least one Goal")
    if len(goal_ids) != len(set(goal_ids)):
        errors.append("duplicate goal_id values")
    if status in PROGRAM_VERIFIED_STATUSES:
        if len(goal_statuses) != len(goal_ids) or any(item not in GOAL_TERMINAL_STATUSES for item in goal_statuses):
            errors.append("PROGRAM_HAS_UNFINISHED_GOALS")

    release = section(text, "release")
    release_values = {
        key: scalar(release, key, 2)
        for key in (
            "integration_status",
            "merge_status",
            "deployment_status",
            "production_verification_status",
        )
    }
    if status == "COMPLETE":
        if release_values["integration_status"] not in {"target_verified", "not_required"}:
            errors.append("Program completion requires verified or unnecessary integration")
        required_by_scope = {
            "branch": (),
            "merged": ("merge_status",),
            "deployed": ("merge_status", "deployment_status"),
            "production_verified": (
                "merge_status",
                "deployment_status",
                "production_verification_status",
            ),
        }
        for key in required_by_scope.get(scope or "", ()):
            if release_values[key] not in {"complete", "verified"}:
                errors.append(f"completion_scope {scope} requires release.{key}")
        candidate = section(text, "candidate")
        for key in ("commit", "evidence_manifest"):
            if not scalar(candidate, key, 2):
                errors.append(f"Program completion requires candidate.{key}")
        if scalar(candidate, "status", 2) != "target_verified":
            errors.append("Program completion requires candidate.status: target_verified")
        if version_at_least(schema_version, (1, 2)):
            receipt = section(text, "completion_receipt")
            if scalar(receipt, "status", 2) != "ready":
                errors.append("COMPLETE_REQUIRES_READY_COMPLETION_RECEIPT")
            for key in ("path", "sha256"):
                if not scalar(receipt, key, 2):
                    errors.append(f"complete Program requires completion_receipt.{key}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
