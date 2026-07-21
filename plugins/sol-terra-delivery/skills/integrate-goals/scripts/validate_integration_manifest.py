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
    "goals",
    "integration_commit",
    "clean_worktree",
    "full_verification_passed",
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
            for key in ("commit_sha", "pushed", "target_verified", "model_routing_valid"):
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

    if not args.allow_empty:
        if not data.get("integration_commit"):
            errors.append("missing integration_commit")
        if data.get("clean_worktree") is not True:
            errors.append("integration worktree is not clean")
        if data.get("full_verification_passed") is not True:
            errors.append("full integration verification has not passed")
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
