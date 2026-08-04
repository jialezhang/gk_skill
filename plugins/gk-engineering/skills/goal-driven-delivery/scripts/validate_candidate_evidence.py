#!/usr/bin/env python3
"""Validate same-candidate coverage and independent Terra or audited fallback acceptance."""

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

EVIDENCE_STATUSES = {
    "draft",
    "candidate",
    "accepted",
    "invalidated",
    "superseded",
}

PROVENANCE_STATUSES = {
    "pending",
    "verified",
    "not_applicable",
    "invalidated",
}


def requires_lifecycle(data: dict[str, object]) -> bool:
    """Keep 1.0 manifests readable while enforcing the 1.1 contract."""
    version = data.get("schema_version")
    if not isinstance(version, str):
        return "evidence_records" in data or "runtime_provenance" in data
    try:
        return tuple(int(part) for part in version.split(".")[:2]) >= (1, 1)
    except ValueError:
        return "evidence_records" in data or "runtime_provenance" in data


def validate_lifecycle(
    data: dict[str, object],
    candidate: object,
    scenarios: list[object],
    errors: list[str],
) -> dict[str, dict[str, object]]:
    records = data.get("evidence_records")
    if not isinstance(records, list):
        errors.append("evidence_records must be a list")
        return {}

    by_id: dict[str, dict[str, object]] = {}
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append(f"evidence record #{index} must be an object")
            continue
        evidence_id = record.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            errors.append(f"evidence record #{index} missing evidence_id")
            continue
        if evidence_id in by_id:
            errors.append(f"duplicate evidence_id: {evidence_id}")
            continue
        by_id[evidence_id] = record
        status = record.get("status")
        if status not in EVIDENCE_STATUSES:
            errors.append(f"{evidence_id}: invalid evidence status")
        if not isinstance(record.get("kind"), str) or not record.get("kind"):
            errors.append(f"{evidence_id}: missing kind")
        if not isinstance(record.get("evidence_path"), str) or not record.get("evidence_path"):
            errors.append(f"{evidence_id}: missing evidence_path")
        if status == "accepted" and record.get("candidate_commit") != candidate:
            errors.append(f"{evidence_id}: ACCEPTED_EVIDENCE_CANDIDATE_MISMATCH")
        if status == "invalidated":
            if not record.get("invalidation_reason") or not record.get("invalidated_by"):
                errors.append(f"{evidence_id}: invalidated evidence requires reason and invalidated_by")
        if status == "superseded" and not record.get("replacement_evidence_id"):
            errors.append(f"{evidence_id}: superseded evidence requires replacement_evidence_id")

    for evidence_id, record in by_id.items():
        replacement = record.get("replacement_evidence_id")
        if replacement and replacement not in by_id:
            errors.append(f"{evidence_id}: replacement_evidence_id does not exist")

    def require_accepted(reference: object, label: str) -> None:
        if not isinstance(reference, str) or not reference:
            errors.append(f"{label}: evidence_id is required")
            return
        record = by_id.get(reference)
        if record is None:
            errors.append(f"{label}: evidence_id is unknown")
        elif record.get("status") != "accepted":
            errors.append(f"{label}: referenced evidence is not accepted")

    for index, scenario in enumerate(scenarios, 1):
        if isinstance(scenario, dict) and scenario.get("status") == "passed":
            require_accepted(scenario.get("evidence_id"), str(scenario.get("scenario_id") or index))
    full = data.get("full_verification")
    if isinstance(full, dict) and full.get("passed") is True:
        require_accepted(full.get("evidence_id"), "full_verification")
    acceptance = data.get("final_acceptance")
    if isinstance(acceptance, dict) and acceptance.get("verdict") == "TARGET_VERIFIED":
        require_accepted(acceptance.get("evidence_id"), "final_acceptance")
    return by_id


def validate_runtime_provenance(
    data: dict[str, object], candidate: object, errors: list[str]
) -> None:
    provenance = data.get("runtime_provenance")
    if not isinstance(provenance, dict):
        errors.append("runtime_provenance must be an object")
        return
    status = provenance.get("status")
    if status not in PROVENANCE_STATUSES:
        errors.append("runtime_provenance has invalid status")
        return
    if status == "not_applicable":
        if not provenance.get("not_applicable_reason"):
            errors.append("runtime_provenance not_applicable requires not_applicable_reason")
        return
    if status != "verified":
        errors.append(f"runtime_provenance must be verified, got {status!r}")
        return
    if provenance.get("candidate_commit") != candidate:
        errors.append("RUNTIME_PROVENANCE_CANDIDATE_MISMATCH")
    for key in ("target_kind", "evidence_path", "observed_at"):
        if not isinstance(provenance.get(key), str) or not provenance.get(key):
            errors.append(f"runtime_provenance verified requires {key}")
    required = provenance.get("required_observation_ids")
    observations = provenance.get("observations")
    if not isinstance(required, list) or not all(isinstance(item, str) and item for item in required):
        errors.append("runtime_provenance required_observation_ids must be non-empty strings")
        required = []
    if not isinstance(observations, list):
        errors.append("runtime_provenance observations must be a list")
        observations = []
    observed: dict[str, object] = {}
    for index, observation in enumerate(observations, 1):
        if not isinstance(observation, dict):
            errors.append(f"runtime provenance observation #{index} must be an object")
            continue
        observation_id = observation.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id:
            errors.append(f"runtime provenance observation #{index} missing observation_id")
            continue
        if observation_id in observed:
            errors.append(f"duplicate runtime provenance observation_id: {observation_id}")
        observed[observation_id] = observation
        if observation.get("status") not in {"passed", "failed", "not_applicable"}:
            errors.append(f"{observation_id}: invalid runtime provenance observation status")
        if not isinstance(observation.get("source"), str) or not observation.get("source"):
            errors.append(f"{observation_id}: runtime provenance observation requires source")
    for observation_id in required:
        observation = observed.get(observation_id)
        if not isinstance(observation, dict) or observation.get("status") != "passed":
            errors.append(f"runtime_provenance required observation is not passed: {observation_id}")


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

    lifecycle_required = requires_lifecycle(data)
    if lifecycle_required:
        validate_lifecycle(data, candidate, scenarios, errors)
        if status == "target_verified" and not args.allow_incomplete:
            validate_runtime_provenance(data, candidate, errors)

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
            acceptance_model = acceptance.get("model")
            acceptance_route = acceptance.get("model_route")
            if acceptance_model != "gpt-5.6-terra" and acceptance_route != "terra_route_fallback":
                errors.append("TERRA_OR_AUDITED_FALLBACK_FINAL_ACCEPTANCE_REQUIRED")
            if acceptance_route == "terra_route_fallback" and acceptance.get(
                "fallback_from_model"
            ) != "gpt-5.6-terra":
                errors.append("final acceptance fallback_from_model must be gpt-5.6-terra")
            reviewer = acceptance.get("reviewer_thread_id")
            reviewer_turn = acceptance.get("reviewer_turn_id")
            implementers = acceptance.get("implementation_thread_ids")
            if not reviewer or not reviewer_turn or not isinstance(implementers, list) or not implementers:
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
