#!/usr/bin/env python3
"""Validate the minimum evidence needed for program integration completion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED = {
    "schema_version",
    "program_id",
    "base_commit",
    "program_state_valid",
    "goals",
    "integration_commit",
    "clean_worktree",
    "full_verification_passed",
    "candidate_evidence_valid",
    "evidence_lifecycle_valid",
    "runtime_provenance",
    "goal_telemetry_snapshots",
    "completion_telemetry",
    "final_acceptance_model",
    "final_acceptance_thread_id",
    "final_acceptance_turn_id",
    "model_routing_log",
    "implementation_thread_ids",
    "final_acceptance_independent",
    "final_acceptance",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        print(f"ERROR: invalid integration manifest: {error}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for key in sorted(REQUIRED - set(data)):
        errors.append(f"missing field: {key}")
    goals = data.get("goals")
    if not isinstance(goals, list):
        errors.append("goals must be a list")
    elif not goals and not args.allow_empty:
        errors.append("goals must contain at least one Goal")
    else:
        for index, goal in enumerate(goals, 1):
            if not isinstance(goal, dict):
                errors.append(f"goal #{index} must be an object")
                continue
            goal_id = goal.get("goal_id") or f"#{index}"
            for key in (
                "commit_sha",
                "pushed",
                "target_verified",
                "model_routing_valid",
                "evidence_lifecycle_valid",
                "completion_telemetry_snapshot",
            ):
                if key not in goal:
                    errors.append(f"{goal_id}: missing {key}")
            if not goal.get("commit_sha"):
                errors.append(f"{goal_id}: missing clean commit_sha")
            if goal.get("pushed") is not True:
                errors.append(f"{goal_id}: commit is not verified as pushed")
            if goal.get("target_verified") is not True:
                errors.append(f"{goal_id}: bounded target is not verified")
            if goal.get("model_routing_valid") is not True:
                errors.append(f"{goal_id}: model routing is not valid")
            if goal.get("evidence_lifecycle_valid") is not True:
                errors.append(f"{goal_id}: evidence lifecycle is not valid")
            if not goal.get("completion_telemetry_snapshot"):
                errors.append(f"{goal_id}: completion telemetry snapshot is missing")

    if not args.allow_empty:
        if not data.get("integration_commit"):
            errors.append("missing integration_commit")
        if data.get("clean_worktree") is not True:
            errors.append("integration worktree is not clean")
        if data.get("full_verification_passed") is not True:
            errors.append("full integration verification has not passed")
        if data.get("program_state_valid") is not True:
            errors.append("program_state has not validated")
        if data.get("candidate_evidence_valid") is not True:
            errors.append("candidate evidence has not validated")
        if data.get("evidence_lifecycle_valid") is not True:
            errors.append("integration evidence lifecycle has not validated")
        provenance = data.get("runtime_provenance")
        if not isinstance(provenance, dict):
            errors.append("runtime_provenance must be an object")
        else:
            if provenance.get("status") != "verified":
                errors.append("integration runtime provenance has not verified")
            if provenance.get("candidate_commit") != data.get("integration_commit"):
                errors.append("integration runtime provenance candidate does not match")
            if not provenance.get("evidence_path"):
                errors.append("integration runtime provenance evidence_path is required")
        telemetry = data.get("goal_telemetry_snapshots")
        if not isinstance(telemetry, list) or not telemetry:
            errors.append("goal_telemetry_snapshots must be a non-empty list")
        else:
            telemetry_goal_ids = {
                item.get("goal_id")
                for item in telemetry
                if isinstance(item, dict) and item.get("snapshot_path")
            }
            for goal in goals if isinstance(goals, list) else []:
                if isinstance(goal, dict) and goal.get("goal_id") not in telemetry_goal_ids:
                    errors.append(f"{goal.get('goal_id')}: telemetry snapshot is not aggregated")
        completion = data.get("completion_telemetry")
        if not isinstance(completion, dict):
            errors.append("completion_telemetry must be an object")
        else:
            if completion.get("status") not in {"captured", "captured_with_unavailable"}:
                errors.append("integration completion telemetry has not captured")
            for key in ("snapshot_path", "captured_at", "source"):
                if not completion.get(key):
                    errors.append(f"integration completion telemetry requires {key}")
        acceptance_model = data.get("final_acceptance_model")
        acceptance_route = data.get("final_acceptance_route")
        if acceptance_model != "gpt-5.6-terra" and acceptance_route != "terra_route_fallback":
            errors.append("TERRA_OR_AUDITED_FALLBACK_FINAL_ACCEPTANCE_REQUIRED")
        if acceptance_route == "terra_route_fallback" and data.get(
            "final_acceptance_fallback_from_model"
        ) != "gpt-5.6-terra":
            errors.append("final acceptance fallback_from_model must be gpt-5.6-terra")
        acceptance_thread = data.get("final_acceptance_thread_id")
        acceptance_turn = data.get("final_acceptance_turn_id")
        routing_log = data.get("model_routing_log")
        implementation_threads = data.get("implementation_thread_ids")
        if not isinstance(implementation_threads, list) or not implementation_threads:
            errors.append("implementation_thread_ids must be a non-empty list")
        elif not acceptance_thread:
            errors.append("final_acceptance_thread_id is required")
        elif acceptance_thread in implementation_threads:
            errors.append("FINAL_ACCEPTANCE_NOT_INDEPENDENT")
        if data.get("final_acceptance_independent") is not True:
            errors.append("final acceptance independence has not validated")
        if not acceptance_turn:
            errors.append("final_acceptance_turn_id is required")
        if not routing_log:
            errors.append("model_routing_log is required")
        if data.get("final_acceptance") != "TARGET_VERIFIED":
            errors.append("final_acceptance must be TARGET_VERIFIED")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
