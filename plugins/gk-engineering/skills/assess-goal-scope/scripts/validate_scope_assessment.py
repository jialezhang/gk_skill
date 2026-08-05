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

REQUIRED_V1_1_TOP_LEVEL = {
    "estimate_basis",
    "base_scenario",
    "readiness_status",
    "readiness_evidence",
    "measurement_evidence",
    "critical_path_p50_hours",
    "cumulative_workload_p50_hours",
    "cumulative_workload_p80_hours",
    "expected_wait_p50_hours",
    "expected_wait_p80_hours",
    "conditional_estimates",
    "risk_correlation_groups",
    "reestimate_required",
    "reestimate_gate",
    "estimate_invalidation_keys",
}

ESTIMATE_BASES = {
    "repository_measurements",
    "historical_actuals",
    "mixed",
    "calibrated_ranges_no_history",
}

READINESS_STATUSES = {
    "verified_materialized",
    "partially_materialized",
    "not_materialized",
    "unknown",
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


def top_level_block(text: str, key: str) -> str:
    match = re.search(
        rf"^{re.escape(key)}:\s*(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def has_list_item(text: str, key: str) -> bool:
    block = top_level_block(text, key)
    return bool(re.search(r"(?m)^\s*-\s+\S", block))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment", type=Path)
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="allow an unfilled template while still checking its structure",
    )
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

    schema_version = scalar(text, "schema_version")
    if schema_version == "1.1":
        for key in sorted(REQUIRED_V1_1_TOP_LEVEL - top_level):
            errors.append(f"schema 1.1 missing top-level key: {key}")

        critical_p50 = number(text, "critical_path_p50_hours", errors)
        critical_p80 = number(text, "critical_path_p80_hours", errors)
        workload_p50 = number(text, "cumulative_workload_p50_hours", errors)
        workload_p80 = number(text, "cumulative_workload_p80_hours", errors)
        wait_p50 = number(text, "expected_wait_p50_hours", errors)
        wait_p80 = number(text, "expected_wait_p80_hours", errors)

        if None not in (critical_p50, p50) and critical_p50 != p50:
            errors.append("schema 1.1 requires critical_path_p50_hours == p50_hours")
        if None not in (critical_p80, p80) and critical_p80 != p80:
            errors.append("schema 1.1 requires critical_path_p80_hours == p80_hours")
        if None not in (workload_p50, workload_p80) and not (0 <= workload_p50 <= workload_p80):
            errors.append("cumulative workload must satisfy 0 <= P50 <= P80")
        if None not in (workload_p50, p50) and workload_p50 < p50:
            errors.append("cumulative_workload_p50_hours cannot be lower than wall-clock p50_hours")
        if None not in (workload_p80, p80) and workload_p80 < p80:
            errors.append("cumulative_workload_p80_hours cannot be lower than wall-clock p80_hours")
        if None not in (wait_p50, wait_p80) and not (0 <= wait_p50 <= wait_p80):
            errors.append("expected wait must satisfy 0 <= P50 <= P80")

        estimate_basis = scalar(text, "estimate_basis")
        readiness_status = scalar(text, "readiness_status")
        if not args.allow_placeholders and estimate_basis not in ESTIMATE_BASES:
            errors.append(f"invalid estimate_basis: {estimate_basis!r}")
        if readiness_status not in READINESS_STATUSES:
            errors.append(f"invalid readiness_status: {readiness_status!r}")
        if not args.allow_placeholders and not scalar(text, "base_scenario"):
            errors.append("schema 1.1 requires a non-empty base_scenario")
        if not args.allow_placeholders and not has_list_item(text, "measurement_evidence"):
            errors.append("schema 1.1 requires measurement_evidence")
        if (
            not args.allow_placeholders
            and readiness_status in {"verified_materialized", "not_materialized"}
            and not has_list_item(text, "readiness_evidence")
        ):
            errors.append(f"readiness_status {readiness_status!r} requires readiness_evidence")

        reestimate_required = scalar(text, "reestimate_required")
        reestimate_gate = scalar(text, "reestimate_gate")
        if readiness_status in {"partially_materialized", "unknown"}:
            if reestimate_required != "true":
                errors.append(f"readiness_status {readiness_status!r} requires reestimate_required: true")
            if reestimate_gate != "G-00":
                errors.append(f"readiness_status {readiness_status!r} requires reestimate_gate: G-00")
            if not args.allow_placeholders and not has_list_item(text, "conditional_estimates"):
                errors.append(f"readiness_status {readiness_status!r} requires conditional_estimates")
            if not args.allow_placeholders and not has_list_item(text, "estimate_invalidation_keys"):
                errors.append(f"readiness_status {readiness_status!r} requires estimate_invalidation_keys")

        if has_list_item(text, "conditional_estimates"):
            conditional_block = top_level_block(text, "conditional_estimates")
            if "risk_correlation_group:" not in conditional_block:
                errors.append("conditional_estimates must identify a risk_correlation_group")
            if not has_list_item(text, "risk_correlation_groups"):
                errors.append("conditional_estimates require risk_correlation_groups for deduplication")

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
