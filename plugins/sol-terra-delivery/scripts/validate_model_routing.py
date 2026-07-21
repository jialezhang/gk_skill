#!/usr/bin/env python3
"""Validate observed per-turn model routing records."""

from __future__ import annotations

import argparse
import json
import sys
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routing_log", type=Path)
    parser.add_argument("--require-canary", action="store_true")
    args = parser.parse_args()

    if not args.routing_log.is_file():
        print(f"ERROR: routing log not found: {args.routing_log}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_turns: set[str] = set()
    canary_models: set[str] = set()
    for line_number, raw in enumerate(args.routing_log.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(f"line {line_number}: invalid JSON: {error.msg}")
            continue

        turn_id = record.get("turn_id")
        task_class = record.get("task_class")
        requested = record.get("requested_model")
        observed = record.get("observed_model")
        verified = record.get("verified")
        reason = record.get("allowed_reason")

        if not isinstance(turn_id, str) or not turn_id:
            errors.append(f"line {line_number}: missing turn_id")
        elif turn_id in seen_turns:
            errors.append(f"line {line_number}: duplicate turn_id: {turn_id}")
        else:
            seen_turns.add(turn_id)

        if requested not in MODELS or observed not in MODELS:
            errors.append(f"line {line_number}: unsupported requested/observed model")
        if verified is not True:
            errors.append(f"line {line_number}: MODEL_ROUTE_UNVERIFIED")
        if requested != observed:
            errors.append(
                f"line {line_number}: MODEL_ROUTE_MISMATCH requested={requested!r} observed={observed!r}"
            )

        if requested == "gpt-5.6-sol" and reason not in SOL_REASONS:
            errors.append(f"line {line_number}: SOL_REASON_NOT_ALLOWED: {reason!r}")
        if task_class in TERRA_TASKS and requested != "gpt-5.6-terra":
            errors.append(f"line {line_number}: {task_class} must request gpt-5.6-terra")
        if task_class in LUNA_TASKS and requested != "gpt-5.6-luna":
            errors.append(f"line {line_number}: {task_class} must request gpt-5.6-luna")
        if task_class == "routing_canary" and requested in MODELS and requested == observed and verified is True:
            canary_models.add(requested)

    if not seen_turns:
        errors.append("routing log contains no turns")
    if args.require_canary:
        missing = sorted(MODELS - canary_models)
        if missing:
            errors.append(f"MODEL_CANARY_INCOMPLETE missing={missing}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.routing_log} ({len(seen_turns)} turns)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
