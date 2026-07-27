#!/usr/bin/env python3
"""Run dependency-free structural checks for the delivery toolkit."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


EXPECTED_SKILLS = {
    "product-to-delivery",
    "create-product-prd",
    "assess-goal-scope",
    "create-implementation-plan",
    "goal-driven-delivery",
    "integrate-goals",
    "review-delivery-gate",
}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def frontmatter(text: str) -> tuple[str | None, str | None]:
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return None, None
    block = match.group(1)
    name = re.search(r"^name:\s*(.+)$", block, flags=re.MULTILINE)
    description = re.search(r"^description:\s*(.+)$", block, flags=re.MULTILINE)
    return (name.group(1).strip() if name else None, description.group(1).strip() if description else None)


def validate_skill(path: Path, errors: list[str]) -> None:
    skill_file = path / "SKILL.md"
    require(skill_file.exists(), f"missing {skill_file}", errors)
    if not skill_file.exists():
        return
    text = skill_file.read_text(encoding="utf-8")
    name, description = frontmatter(text)
    require(name == path.name, f"skill name mismatch in {skill_file}: {name!r}", errors)
    require(bool(description), f"missing description in {skill_file}", errors)
    placeholder = "[" + "TODO"
    require(placeholder not in text, f"placeholder remains in {skill_file}", errors)
    require(len(text.splitlines()) <= 500, f"{skill_file} exceeds 500 lines", errors)
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        require((path / target).exists(), f"broken reference {target} in {skill_file}", errors)


def manifest_value(text: str, section: str, key: str) -> str | None:
    pattern = rf"(?ms)^\s*{re.escape(section)}:\s*\n(?:^[ \t]+.*\n)*?^[ \t]+{re.escape(key)}:\s*[\"']?([^\"'\n]+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def main() -> int:
    plugin_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    plugin_json = plugin_root / ".codex-plugin" / "plugin.json"
    require(plugin_json.exists(), "missing plugin.json", errors)
    if plugin_json.exists():
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        require(data.get("name") == "sol-terra-delivery", "plugin id mismatch", errors)
        require(data.get("skills") == "./skills/", "plugin skills path mismatch", errors)

    skill_root = plugin_root / "skills"
    actual = {item.name for item in skill_root.iterdir() if item.is_dir()}
    require(actual == EXPECTED_SKILLS, f"unexpected skill set: {sorted(actual)}", errors)
    for name in sorted(EXPECTED_SKILLS):
        validate_skill(skill_root / name, errors)

    required_files = [
        "scripts/validate_completion_gate.py",
        "scripts/validate_completion_telemetry.py",
        "spec-kit/preset/preset.yml",
        "spec-kit/preset/templates/spec-template.md",
        "spec-kit/preset/templates/scope-assessment-template.yaml",
        "spec-kit/preset/templates/plan-template.md",
        "spec-kit/preset/templates/tasks-template.md",
        "spec-kit/extension/extension.yml",
        "spec-kit/workflow/workflow.yml",
        "spec-kit/bundle/bundle.yml",
        "spec-kit/bundle/README.md",
    ]
    for relative in required_files:
        require((plugin_root / relative).exists(), f"missing {relative}", errors)

    preset = (plugin_root / "spec-kit/preset/preset.yml").read_text(encoding="utf-8")
    extension = (plugin_root / "spec-kit/extension/extension.yml").read_text(encoding="utf-8")
    workflow = (plugin_root / "spec-kit/workflow/workflow.yml").read_text(encoding="utf-8")
    bundle = (plugin_root / "spec-kit/bundle/bundle.yml").read_text(encoding="utf-8")
    require(manifest_value(preset, "preset", "id") == "sol-terra-artifacts", "preset id mismatch", errors)
    require(manifest_value(extension, "extension", "id") == "delivery-governance", "extension id mismatch", errors)
    require(manifest_value(workflow, "workflow", "id") == "sol-terra-pre-delivery", "workflow id mismatch", errors)
    for component in ("sol-terra-artifacts", "delivery-governance", "sol-terra-pre-delivery"):
        require(component in bundle, f"bundle omits {component}", errors)
    require("$create-product-prd" in workflow, "workflow does not invoke create-product-prd", errors)
    require("$assess-goal-scope" in workflow, "workflow does not invoke assess-goal-scope", errors)
    require("$create-implementation-plan" in workflow, "workflow does not invoke create-implementation-plan", errors)

    text_suffixes = {".md", ".yaml", ".yml", ".json", ".py"}
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in plugin_root.rglob("*")
        if path.is_file() and path.suffix in text_suffixes and "__pycache__" not in path.parts
    )
    placeholder = "[" + "TODO"
    require(placeholder not in all_text, "toolkit contains TODO placeholders", errors)

    fixture = plugin_root / "tests" / "fixtures" / "valid"
    checks = [
        [
            sys.executable,
            str(skill_root / "assess-goal-scope" / "scripts" / "validate_scope_assessment.py"),
            str(skill_root / "assess-goal-scope" / "assets" / "scope-assessment-template.yaml"),
        ],
        [
            sys.executable,
            str(skill_root / "create-product-prd" / "scripts" / "validate_prd.py"),
            str(skill_root / "create-product-prd" / "assets" / "prd-template.md"),
            "--allow-placeholders",
        ],
        [
            sys.executable,
            str(skill_root / "create-implementation-plan" / "scripts" / "validate_plan_artifacts.py"),
            "--prd",
            str(fixture / "spec.md"),
            "--plan",
            str(fixture / "plan.md"),
            "--tasks",
            str(fixture / "tasks.md"),
            "--verification",
            str(fixture / "verification.md"),
        ],
        [
            sys.executable,
            str(skill_root / "goal-driven-delivery" / "scripts" / "validate_delivery_state.py"),
            str(skill_root / "goal-driven-delivery" / "assets" / "delivery-state-template.yaml"),
            "--allow-empty",
        ],
        [
            sys.executable,
            str(skill_root / "product-to-delivery" / "scripts" / "validate_program_state.py"),
            str(skill_root / "product-to-delivery" / "assets" / "program-state-template.yaml"),
            "--allow-empty",
        ],
        [
            sys.executable,
            str(skill_root / "goal-driven-delivery" / "scripts" / "validate_candidate_evidence.py"),
            str(skill_root / "goal-driven-delivery" / "assets" / "candidate-evidence-template.json"),
            "--allow-incomplete",
        ],
        [
            sys.executable,
            str(skill_root / "integrate-goals" / "scripts" / "validate_integration_manifest.py"),
            str(skill_root / "integrate-goals" / "assets" / "program-integration-template.json"),
            "--allow-empty",
        ],
        [sys.executable, str(plugin_root / "tests" / "test_delivery_policy.py")],
        [sys.executable, str(plugin_root / "tests" / "test_delivery_policy_v2.py")],
    ]
    for command in checks:
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode != 0:
            errors.append(f"validator failed: {' '.join(command)}\n{result.stderr.strip()}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: validated plugin, {len(EXPECTED_SKILLS)} skills, and Spec Kit components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
