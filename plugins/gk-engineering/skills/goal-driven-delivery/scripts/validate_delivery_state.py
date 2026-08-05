#!/usr/bin/env python3
"""Validate the required top-level contract of delivery-state.yaml."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_contract import (  # noqa: E402
    DELIVERY_STATUSES,
    DELIVERY_VERIFIED_STATUSES,
    version_at_least,
)


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "delivery_id",
    "status",
    "controller",
    "program",
    "goal",
    "artifacts",
    "target_identity",
    "model_routing_log",
    "model_canary_status",
    "model_handshake_status",
    "agent_budget",
    "tasks",
    "gates",
    "checkpoints",
    "attempts",
    "active_agents",
    "progress",
    "candidate",
    "stage_user_journeys",
    "test_evidence",
    "completion_telemetry",
    "escalations",
    "decisions",
    "evidence",
    "stale_items",
    "next_actions",
    "created_at",
    "updated_at",
}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    if not args.state.is_file():
        print(f"ERROR: state file not found: {args.state}", file=sys.stderr)
        return 1

    text = args.state.read_text(encoding="utf-8")
    errors: list[str] = []
    top_level = set(re.findall(r"^([a-zA-Z0-9_]+):", text, re.MULTILINE))
    version_match = re.search(r'^schema_version:\s*["\']?([^"\'\n]+)', text, re.MULTILINE)
    schema_version = version_match.group(1).strip() if version_match else None
    required_top_level = set(REQUIRED_TOP_LEVEL)
    if version_at_least(schema_version, (1, 3)):
        required_top_level.update({"project_profile_path", "completion_receipt"})
    for key in sorted(required_top_level - top_level):
        errors.append(f"missing top-level key: {key}")

    status_match = re.search(r"^status:\s*([A-Z_]+)\s*$", text, re.MULTILINE)
    status = status_match.group(1) if status_match else None
    if status not in DELIVERY_STATUSES:
        errors.append(f"invalid delivery status: {status!r}")

    if not args.allow_empty:
        for pattern, label in (
            (r'^delivery_id:\s*"?([^"\n]+)', "delivery_id"),
            (r'^\s{2}objective:\s*"?([^"\n]+)', "goal.objective"),
            (r'^\s{2}prd_version:\s*"?([^"\n]+)', "artifacts.prd_version"),
            (r'^\s{2}plan_version:\s*"?([^"\n]+)', "artifacts.plan_version"),
        ):
            match = re.search(pattern, text, re.MULTILINE)
            if not match or not match.group(1).strip():
                errors.append(f"missing runtime value: {label}")

    split_match = re.search(
        r"(?ms)^program:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
        text,
    )
    program_block = split_match.group(1) if split_match else ""
    split_decision = re.search(
        r"^\s{2}split_decision:\s*([a-z_]+)\s*$",
        program_block,
        re.MULTILINE,
    )
    if (
        split_decision
        and split_decision.group(1) != "single_goal"
        and status == "COMPLETE"
    ):
        errors.append("MULTI_GOAL_MILESTONE_CANNOT_COMPLETE_PROGRAM")

    attempt_ids = re.findall(r"^\s+attempt_id:\s*[\"']?([^\"'\n]+)", text, re.MULTILINE)
    if len(attempt_ids) != len(set(attempt_ids)):
        errors.append("duplicate attempt_id values")

    if status in DELIVERY_VERIFIED_STATUSES:
        nonterminal_scan = text
        if status in {"TARGET_VERIFIED", "GOAL_TARGET_VERIFIED"}:
            nonterminal_scan = re.sub(
                r"(?ms)^completion_receipt:\s*\n.*?(?=^[a-zA-Z0-9_]+:|\Z)",
                "",
                nonterminal_scan,
            )
        if re.search(r"^\s+status:\s*(?:pending|ready|assigned|in_progress|needs_rework|plan_conflict|blocked)\s*$", nonterminal_scan, re.MULTILINE):
            errors.append("terminal delivery status contains nonterminal task/gate state")
        for key in ("model_canary_status", "model_handshake_status"):
            match = re.search(rf"^{key}:\s*([a-z_]+)\s*$", text, re.MULTILINE)
            if not match or match.group(1) not in {"passed", "verified"}:
                errors.append(f"terminal Goal requires {key}: passed")
        program_state = re.search(
            r'^\s{2}program_state_path:\s*[\"\']?([^\"\'\n]*)',
            program_block,
            re.MULTILINE,
        )
        if not program_state or not program_state.group(1).strip():
            errors.append("terminal Goal requires program.program_state_path")
        candidate_match = re.search(
            r"(?ms)^candidate:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
            text,
        )
        candidate_block = candidate_match.group(1) if candidate_match else ""
        for key in ("commit", "evidence_manifest"):
            match = re.search(
                rf'^\s{{2}}{key}:\s*[\"\']?([^\"\'\n]*)',
                candidate_block,
                re.MULTILINE,
            )
            if not match or not match.group(1).strip():
                errors.append(f"terminal Goal requires candidate.{key}")
        if not re.search(
            r"^\s{2}status:\s*target_verified\s*$",
            candidate_block,
            re.MULTILINE,
        ):
            errors.append("terminal Goal requires candidate.status: target_verified")
        evidence_match = re.search(
            r"(?ms)^test_evidence:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
            text,
        )
        evidence_block = evidence_match.group(1) if evidence_match else ""
        for key in ("baseline_manifest", "impact_map", "evidence_index"):
            match = re.search(
                rf'^\s{{2}}{key}:\s*[\"\']?([^\"\'\n]*)',
                evidence_block,
                re.MULTILINE,
            )
            if not match or not match.group(1).strip():
                errors.append(f"terminal Goal requires test_evidence.{key}")
        telemetry_match = re.search(
            r"(?ms)^completion_telemetry:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
            text,
        )
        telemetry_block = telemetry_match.group(1) if telemetry_match else ""
        telemetry_status = re.search(
            r"^\s{2}status:\s*([a-z_]+)\s*$", telemetry_block, re.MULTILINE
        )
        if not telemetry_status or telemetry_status.group(1) not in {
            "captured",
            "captured_with_unavailable",
        }:
            errors.append("terminal Goal requires completion_telemetry.status: captured")
        for key in ("snapshot_path", "captured_at", "source"):
            match = re.search(
                rf'^\s{{2}}{key}:\s*["\']?([^"\'\n]*)',
                telemetry_block,
                re.MULTILINE,
            )
            if not match or not match.group(1).strip():
                errors.append(f"terminal Goal requires completion_telemetry.{key}")
        if version_at_least(schema_version, (1, 3)):
            profile = re.search(
                r'^project_profile_path:\s*["\']?([^"\'\n]*)', text, re.MULTILINE
            )
            if not profile or not profile.group(1).strip():
                errors.append("verified Goal requires project_profile_path")
        if status == "COMPLETE" and version_at_least(schema_version, (1, 3)):
            receipt_block = re.search(
                r"(?ms)^completion_receipt:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
                text,
            )
            receipt = receipt_block.group(1) if receipt_block else ""
            if not re.search(r"^\s{2}status:\s*ready\s*$", receipt, re.MULTILINE):
                errors.append("COMPLETE_REQUIRES_READY_COMPLETION_RECEIPT")
            for key in ("path", "sha256"):
                match = re.search(
                    rf'^\s{{2}}{key}:\s*["\']?([^"\'\n]*)', receipt, re.MULTILINE
                )
                if not match or not match.group(1).strip():
                    errors.append(f"complete Goal requires completion_receipt.{key}")

    progress_match = re.search(
        r"(?ms)^progress:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)",
        text,
    )
    progress_block = progress_match.group(1) if progress_match else ""
    for lane in ("implementation", "automation", "exact_target", "release"):
        completed = re.search(
            rf"^\s{{2}}{lane}_completed:\s*(\d+)\s*$",
            progress_block,
            re.MULTILINE,
        )
        total = re.search(
            rf"^\s{{2}}{lane}_total:\s*(\d+)\s*$",
            progress_block,
            re.MULTILINE,
        )
        if not completed or not total:
            errors.append(f"missing progress denominator: {lane}")
            continue
        if int(completed.group(1)) > int(total.group(1)):
            errors.append(f"invalid progress denominator: {lane}")
        if (
            status in DELIVERY_VERIFIED_STATUSES
            and completed.group(1) != total.group(1)
        ):
            errors.append(f"terminal Goal has incomplete progress: {lane}")

    budget_values: dict[str, int] = {}
    for key in (
        "normal_target",
        "soft_limit",
        "hard_limit",
        "spawned_total",
        "max_nesting_depth",
        "max_parallel_goal_sessions",
    ):
        match = re.search(rf"^\s{{2}}{key}:\s*(\d+)\s*$", text, re.MULTILINE)
        if not match:
            errors.append(f"missing agent_budget.{key}")
        else:
            budget_values[key] = int(match.group(1))
    expected_budget = {
        "normal_target": 8,
        "soft_limit": 12,
        "hard_limit": 20,
        "max_nesting_depth": 1,
        "max_parallel_goal_sessions": 3,
    }
    for key, expected in expected_budget.items():
        if key in budget_values and budget_values[key] != expected:
            errors.append(f"agent_budget.{key} must be {expected}")
    if budget_values.get("spawned_total", 0) > budget_values.get("hard_limit", 20):
        errors.append("AGENT_BUDGET_EXHAUSTED: spawned_total exceeds hard_limit")

    checkpoint_blocks = re.findall(
        r"(?ms)^\s{2}- checkpoint_id:\s*([^\n]+)\n(.*?)(?=^\s{2}- checkpoint_id:|\Z)",
        text,
    )
    for raw_id, block in checkpoint_blocks:
        checkpoint_id = raw_id.strip().strip("\"'")
        if not re.search(r"^\s{4}status:\s*completed\s*$", block, re.MULTILINE):
            continue
        commit = re.search(r"^\s{4}commit_sha:\s*[\"']?([^\"'\n]*)", block, re.MULTILINE)
        pushed = re.search(r"^\s{4}pushed:\s*true\s*$", block, re.MULTILINE)
        reported = re.search(r"^\s{4}reported_at:\s*[\"']?([^\"'\n]*)", block, re.MULTILINE)
        if not commit or not commit.group(1).strip() or not pushed or not reported or not reported.group(1).strip():
            errors.append(
                f"completed checkpoint {checkpoint_id} requires commit_sha, pushed: true, and reported_at"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
