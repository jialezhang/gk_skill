#!/usr/bin/env python3
"""Validate same-candidate coverage and independent Terra or audited fallback acceptance."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_contract import (  # noqa: E402
    EVIDENCE_STATUSES,
    EXTERNAL_EFFECT_POLICIES,
    LEGACY_PROVIDER_MODES,
    PROVENANCE_STATUSES,
    file_digest,
    version_at_least,
)


def requires_lifecycle(data: dict[str, object]) -> bool:
    """Keep 1.0 manifests readable while enforcing the 1.1 contract."""
    version = data.get("schema_version")
    if not isinstance(version, str):
        return "evidence_records" in data or "runtime_provenance" in data
    return version_at_least(version, (1, 1))


def evidence_supports_candidate(record: dict[str, object], candidate: object) -> bool:
    if record.get("candidate_commit") == candidate:
        return True
    revalidation = record.get("revalidation")
    return (
        isinstance(revalidation, dict)
        and revalidation.get("candidate_commit") == candidate
        and revalidation.get("result") == "accepted"
        and isinstance(revalidation.get("validated_at"), str)
        and bool(revalidation.get("validated_at"))
        and isinstance(revalidation.get("invalidation_keys_checked"), list)
        and bool(revalidation.get("invalidation_keys_checked"))
        and all(
            isinstance(item, str) and item
            for item in revalidation.get("invalidation_keys_checked", [])
        )
        and isinstance(revalidation.get("evidence_path"), str)
        and bool(revalidation.get("evidence_path"))
    )


def validate_candidate_freeze(
    data: dict[str, object],
    candidate: object,
    profile_path: Path | None,
    errors: list[str],
) -> None:
    freeze = data.get("candidate_freeze")
    if not isinstance(freeze, dict):
        errors.append("CANDIDATE_FREEZE_REQUIRED")
        return
    if freeze.get("status") != "frozen" or freeze.get("candidate_commit") != candidate:
        errors.append("CANDIDATE_FREEZE_MISMATCH")
    for key in ("frozen_at", "project_profile_path"):
        if not isinstance(freeze.get(key), str) or not freeze.get(key):
            errors.append(f"candidate_freeze requires {key}")
    expected_profile_digest = freeze.get("project_profile_sha256")
    if not isinstance(expected_profile_digest, str) or not expected_profile_digest:
        errors.append("candidate_freeze requires project_profile_sha256")
    elif profile_path is not None and profile_path.is_file():
        actual_profile_digest = file_digest(profile_path)
        if actual_profile_digest != expected_profile_digest:
            errors.append(
                "PROJECT_PROFILE_DIGEST_MISMATCH "
                f"expected={expected_profile_digest} actual={actual_profile_digest}"
            )
    unresolved = freeze.get("unresolved_effect_ids")
    if not isinstance(unresolved, list):
        errors.append("candidate_freeze.unresolved_effect_ids must be a list")
    elif unresolved:
        errors.append("candidate freeze has unresolved external effects")


def validate_external_effects(
    scenario: dict[str, object],
    label: str,
    declared_effects: dict[str, str],
    errors: list[str],
) -> None:
    effects = scenario.get("external_effects")
    if not isinstance(effects, list):
        errors.append(f"{label}: external_effects must be a list")
        return
    seen: set[str] = set()
    for index, effect in enumerate(effects, 1):
        if not isinstance(effect, dict):
            errors.append(f"{label}: external effect #{index} must be an object")
            continue
        effect_id = effect.get("effect_id")
        if not isinstance(effect_id, str) or not effect_id:
            errors.append(f"{label}: external effect #{index} missing effect_id")
            continue
        if effect_id in seen:
            errors.append(f"{label}: duplicate external effect {effect_id}")
        seen.add(effect_id)
        policy = effect.get("policy")
        if policy not in EXTERNAL_EFFECT_POLICIES:
            errors.append(f"{label}: {effect_id} has invalid policy")
        declared_policy = declared_effects.get(effect_id)
        if declared_policy is None:
            errors.append(f"{label}: EXTERNAL_EFFECT_NOT_DECLARED {effect_id}")
        elif declared_policy != policy:
            errors.append(
                f"{label}: EXTERNAL_EFFECT_POLICY_MISMATCH "
                f"{effect_id} profile={declared_policy} scenario={policy}"
            )
        if policy in {"sandboxed", "authorized"} and (
            not isinstance(effect.get("evidence_path"), str)
            or not effect.get("evidence_path")
        ):
            errors.append(f"{label}: {effect_id} requires effect evidence")
        if policy == "authorized" and (
            not isinstance(effect.get("authorization_ref"), str)
            or not effect.get("authorization_ref")
        ):
            errors.append(f"{label}: {effect_id} requires authorization_ref")


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
        if status == "accepted" and not evidence_supports_candidate(record, candidate):
            errors.append(f"{evidence_id}: EVIDENCE_REVALIDATION_REQUIRED")
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
        elif not evidence_supports_candidate(record, candidate):
            errors.append(f"{label}: referenced evidence is not valid for candidate")

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
    parser.add_argument("--project-profile", type=Path)
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
    profile_path = args.project_profile
    freeze = data.get("candidate_freeze")
    if profile_path is None and isinstance(freeze, dict):
        raw_profile_path = freeze.get("project_profile_path")
        if isinstance(raw_profile_path, str) and raw_profile_path:
            candidate_profile = Path(raw_profile_path)
            profile_path = (
                candidate_profile
                if candidate_profile.is_absolute()
                else args.manifest.parent / candidate_profile
            )
    declared_effects: dict[str, str] = {}
    if profile_path is not None and profile_path.is_file():
        profile_result = subprocess.run(
            [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "validate_project_profile.py"),
                str(profile_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if profile_result.returncode != 0:
            errors.extend(
                f"project profile: {line}"
                for line in (profile_result.stderr or profile_result.stdout).splitlines()
                if line
            )
        try:
            profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            profile_data = {}
        for effect in profile_data.get("external_effects", []) if isinstance(profile_data, dict) else []:
            if isinstance(effect, dict) and isinstance(effect.get("effect_id"), str):
                declared_effects[str(effect["effect_id"])] = str(effect.get("policy", ""))
    elif (
        version_at_least(data.get("schema_version"), (1, 2))
        and data.get("status") == "target_verified"
        and not args.allow_incomplete
    ):
        errors.append(f"PROJECT_PROFILE_REQUIRED {profile_path}")
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
        if version_at_least(data.get("schema_version"), (1, 2)):
            validate_external_effects(
                scenario, str(scenario_id or index), declared_effects, errors
            )
        else:
            provider_mode = scenario.get("provider_mode")
            if provider_mode not in LEGACY_PROVIDER_MODES:
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
        if version_at_least(data.get("schema_version"), (1, 2)):
            validate_candidate_freeze(data, candidate, profile_path, errors)
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
