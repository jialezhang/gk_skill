#!/usr/bin/env python3
"""Validate the deterministic fields of scope-assessment.yaml."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "assessment_id",
    "p50_hours",
    "p80_hours",
    "p90_hours",
    "expected_files",
    "domains",
    "uncertainty",
    "parallelizable",
    "suggested_goals",
    "critical_path_p80_hours",
    "split_recommended",
    "split_strength",
    "split_decision",
    "decision_source",
    "decision_timeout_seconds",
    "work_packages",
    "dependency_graph",
    "conflict_graph",
    "created_at",
}


def scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*[\"']?([^\"'\n]+)", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def number(text: str, key: str, errors: list[str]) -> float | None:
    raw = scalar(text, key)
    try:
        return float(raw) if raw is not None else None
    except ValueError:
        errors.append(f"{key} must be numeric")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment", type=Path)
    args = parser.parse_args()

    if not args.assessment.is_file():
        print(f"ERROR: assessment not found: {args.assessment}", file=sys.stderr)
        return 1

    text = args.assessment.read_text(encoding="utf-8")
    errors: list[str] = []
    top_level = set(re.findall(r"^([a-zA-Z0-9_]+):", text, re.MULTILINE))
    for key in sorted(REQUIRED_TOP_LEVEL - top_level):
        errors.append(f"missing top-level key: {key}")

    p50 = number(text, "p50_hours", errors)
    p80 = number(text, "p80_hours", errors)
    p90 = number(text, "p90_hours", errors)
    if None not in (p50, p80, p90) and not (0 <= p50 <= p80 <= p90):
        errors.append("duration percentiles must satisfy 0 <= p50_hours <= p80_hours <= p90_hours")

    split_recommended = scalar(text, "split_recommended")
    split_strength = scalar(text, "split_strength")
    if p80 is not None and p80 > 8 and split_recommended != "true":
        errors.append("p80_hours > 8 requires split_recommended: true")
    if p80 is not None and p80 > 10 and split_strength != "strong":
        errors.append("p80_hours > 10 requires split_strength: strong")

    decision = scalar(text, "split_decision")
    source = scalar(text, "decision_source")
    timeout = number(text, "decision_timeout_seconds", errors)
    if decision not in {"awaiting_user", "split", "single_goal"}:
        errors.append(f"invalid split_decision: {decision!r}")
    if source not in {"pending", "explicit_user", "timeout_default_single", "not_required"}:
        errors.append(f"invalid decision_source: {source!r}")
    if source == "timeout_default_single" and decision != "single_goal":
        errors.append("timeout_default_single requires split_decision: single_goal")
    if source == "timeout_default_single" and timeout != 240:
        errors.append("timeout_default_single requires decision_timeout_seconds: 240")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.assessment}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
