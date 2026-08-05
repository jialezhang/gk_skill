#!/usr/bin/env python3
"""Validate the declarative, project-agnostic delivery profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from delivery_contract import EXTERNAL_EFFECT_POLICIES


REQUIRED_COLLECTIONS = {
    "target_components",
    "protected_resources",
    "external_effects",
    "acceptance_journeys",
    "verification_commands",
    "rollback_actions",
}


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def object_list(data: dict[str, object], key: str, errors: list[str]) -> list[dict[str, object]]:
    value = data.get(key)
    if not isinstance(value, list):
        errors.append(f"{key} must be a list")
        return []
    result: list[dict[str, object]] = []
    for index, item in enumerate(value, 1):
        if not isinstance(item, dict):
            errors.append(f"{key} item #{index} must be an object")
        else:
            result.append(item)
    return result


def collect_ids(
    items: list[dict[str, object]], key: str, label: str, errors: list[str]
) -> set[str]:
    identifiers: set[str] = set()
    for index, item in enumerate(items, 1):
        identifier = item.get(key)
        if not nonempty(identifier):
            errors.append(f"{label} #{index} missing {key}")
            continue
        assert isinstance(identifier, str)
        if identifier in identifiers:
            errors.append(f"duplicate {key}: {identifier}")
        identifiers.add(identifier)
    return identifiers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    if not args.profile.is_file():
        print(f"ERROR: project profile not found: {args.profile}", file=sys.stderr)
        return 1
    try:
        data = json.loads(args.profile.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: invalid project profile: {error}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("ERROR: project profile root must be an object", file=sys.stderr)
        return 1

    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("unsupported project profile schema_version")
    if not args.allow_empty and not nonempty(data.get("profile_id")):
        errors.append("profile_id is required")
    for key in sorted(REQUIRED_COLLECTIONS - set(data)):
        errors.append(f"missing project profile key: {key}")

    components = object_list(data, "target_components", errors)
    resources = object_list(data, "protected_resources", errors)
    effects = object_list(data, "external_effects", errors)
    journeys = object_list(data, "acceptance_journeys", errors)
    commands = object_list(data, "verification_commands", errors)
    rollbacks = object_list(data, "rollback_actions", errors)

    component_ids = collect_ids(components, "component_id", "target component", errors)
    resource_ids = collect_ids(resources, "resource_id", "protected resource", errors)
    collect_ids(effects, "effect_id", "external effect", errors)
    collect_ids(journeys, "journey_id", "acceptance journey", errors)
    collect_ids(commands, "command_id", "verification command", errors)
    rollback_ids = collect_ids(rollbacks, "action_id", "rollback action", errors)

    if not args.allow_empty:
        if not components:
            errors.append("project profile requires at least one target component")
        if not journeys:
            errors.append("project profile requires at least one acceptance journey")
        if not commands:
            errors.append("project profile requires at least one verification command")

    for component in components:
        identifier = component.get("component_id", "target component")
        if not nonempty(component.get("kind")):
            errors.append(f"{identifier}: target component requires kind")
        for key in ("identity_requirements", "runtime_probes"):
            value = component.get(key)
            if not isinstance(value, list) or not all(nonempty(item) for item in value):
                errors.append(f"{identifier}: {key} must be a string list")

    for resource in resources:
        identifier = resource.get("resource_id", "protected resource")
        required = ("locator", "write_gate", "backup_action", "rollback_action")
        if any(not nonempty(resource.get(key)) for key in required):
            errors.append(f"{identifier}: PROTECTED_RESOURCE_GATE_INCOMPLETE")
        rollback = resource.get("rollback_action")
        if nonempty(rollback) and rollback not in rollback_ids:
            errors.append(f"{identifier}: unknown rollback_action {rollback}")

    for effect in effects:
        identifier = effect.get("effect_id", "external effect")
        policy = effect.get("policy")
        if policy not in EXTERNAL_EFFECT_POLICIES:
            errors.append(f"{identifier}: invalid external effect policy")
        if policy == "authorized" and not nonempty(effect.get("authorization_ref")):
            errors.append(f"{identifier}: authorized effect requires authorization_ref")
        budget = effect.get("budget_limit")
        if budget is not None and (not isinstance(budget, (int, float)) or budget < 0):
            errors.append(f"{identifier}: budget_limit must be null or non-negative")
        if not nonempty(effect.get("verification_mode")):
            errors.append(f"{identifier}: external effect requires verification_mode")

    for journey in journeys:
        identifier = journey.get("journey_id", "acceptance journey")
        claims = journey.get("claim_ids")
        targets = journey.get("target_component_ids")
        if not isinstance(claims, list) or not claims or not all(nonempty(item) for item in claims):
            errors.append(f"{identifier}: claim_ids must be a non-empty string list")
        if not isinstance(targets, list) or not targets or not all(nonempty(item) for item in targets):
            errors.append(f"{identifier}: target_component_ids must be a non-empty string list")
        elif unknown := sorted(set(targets) - component_ids):
            errors.append(f"{identifier}: unknown target components {unknown}")

    for command in commands:
        identifier = command.get("command_id", "verification command")
        if not nonempty(command.get("command")) or command.get("tier") not in {
            "fast",
            "change",
            "full",
        }:
            errors.append(f"{identifier}: invalid verification command")

    for rollback in rollbacks:
        identifier = rollback.get("action_id", "rollback action")
        if not nonempty(rollback.get("command")):
            errors.append(f"{identifier}: rollback action requires command")
        applies_to = rollback.get("applies_to")
        if not isinstance(applies_to, list) or not all(nonempty(item) for item in applies_to):
            errors.append(f"{identifier}: applies_to must be a string list")
        elif unknown := sorted(set(applies_to) - resource_ids):
            errors.append(f"{identifier}: unknown protected resources {unknown}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
