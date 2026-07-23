#!/usr/bin/env python3
"""Validate same-candidate scenario coverage and independent Terra acceptance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROVIDER_MODES = {
    "mock",
    "sandbox",
    "real_free",
    "real_expensive",
    "not_applicable",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"ERROR: candidate evidence not found: {args.manifest}", file=sys.stderr)
        return 1
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: invalid candidate evidence: {error}", file=sys.stderr)
        return 1

    errors: list[str] = []
    candidate = data.get("candidate_commit")
    claims = data.get("acceptance_claims")
    scenarios = data.get("execution_scenarios")
    if (not isinstance(candidate, str) or not candidate) and not args.allow_incomplete:
        errors.append("missing candidate_commit")
    if not isinstance(claims, list):
        errors.append("acceptance_claims must be a list")
        claims = []
    if not isinstance(scenarios, list):
        errors.append("execution_scenarios must be a list")
        scenarios = []

    covered: set[str] = set()
    scenario_ids: set[str] = set()
    for index, scenario in enumerate(scenarios, 1):
        if not isinstance(scenario, dict):
            errors.append(f"scenario #{index} must be an object")
            continue
        scenario_id = scenario.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"scenario #{index} missing scenario_id")
        elif scenario_id in scenario_ids:
            errors.append(f"duplicate scenario_id: {scenario_id}")
        else:
            scenario_ids.add(scenario_id)
        if scenario.get("candidate_commit") != candidate:
            errors.append(f"{scenario_id or index}: CANDIDATE_EVIDENCE_MISMATCH")
        proves = scenario.get("proves")
        if not isinstance(proves, list) or not proves:
            errors.append(f"{scenario_id or index}: proves must be non-empty")
        elif scenario.get("status") == "passed":
            covered.update(str(item) for item in proves)
        provider_mode = scenario.get("provider_mode")
        if provider_mode not in PROVIDER_MODES:
            errors.append(f"{scenario_id or index}: invalid provider_mode")
        if provider_mode == "real_expensive" and not scenario.get("provider_budget"):
            errors.append(f"{scenario_id or index}: real_expensive requires provider_budget")

    unresolved = [
        item
        for item in data.get("invalidations", [])
        if isinstance(item, dict) and item.get("resolved") is not True
    ]
    status = data.get("status")
    if status == "target_verified" and unresolved:
        errors.append("candidate has unresolved evidence invalidations")

    if status == "target_verified" and not args.allow_incomplete:
        missing = sorted(set(str(item) for item in claims) - covered)
        if missing:
            errors.append(f"acceptance claims lack same-candidate passed scenarios: {missing}")
        full = data.get("full_verification")
        if not isinstance(full, dict) or full.get("passed") is not True:
            errors.append("target_verified requires passed full_verification")
        elif full.get("candidate_commit") != candidate:
            errors.append("full_verification candidate does not match")
        acceptance = data.get("final_acceptance")
        if not isinstance(acceptance, dict):
            errors.append("missing final_acceptance")
        else:
            if acceptance.get("candidate_commit") != candidate:
                errors.append("final_acceptance candidate does not match")
            if acceptance.get("model") != "gpt-5.6-terra":
                errors.append("TERRA_FINAL_ACCEPTANCE_REQUIRED")
            reviewer = acceptance.get("reviewer_thread_id")
            implementers = acceptance.get("implementation_thread_ids")
            if not reviewer or not isinstance(implementers, list) or not implementers:
                errors.append("final acceptance identity is incomplete")
            elif reviewer in implementers:
                errors.append("FINAL_ACCEPTANCE_NOT_INDEPENDENT")
            if acceptance.get("independence_verified") is not True:
                errors.append("final acceptance independence is not verified")
            if acceptance.get("verdict") != "TARGET_VERIFIED":
                errors.append("final acceptance verdict must be TARGET_VERIFIED")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
