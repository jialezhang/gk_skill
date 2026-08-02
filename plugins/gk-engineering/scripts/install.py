#!/usr/bin/env python3
"""Install the Codex plugin and local Spec Kit components."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


PLUGIN_ID = "gk-engineering"
MARKETPLACE_ID = "gk-skill"
PRESET_ID = "sol-terra-artifacts"
EXTENSION_ID = "delivery-governance"
WORKFLOW_ID = "sol-terra-pre-delivery"


def run(command: list[str], *, cwd: Path, dry_run: bool, capture: bool = False) -> str:
    rendered = " ".join(command)
    print(f"+ ({cwd}) {rendered}")
    if dry_run:
        return ""
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout or ""


def json_command(command: list[str], *, cwd: Path, dry_run: bool) -> dict:
    if dry_run:
        run(command, cwd=cwd, dry_run=True)
        return {}
    output = run(command, cwd=cwd, dry_run=False, capture=True)
    return json.loads(output)


def contains_component(command: list[str], component_id: str, *, cwd: Path, dry_run: bool) -> bool:
    if dry_run:
        run(command, cwd=cwd, dry_run=True)
        return False
    output = run(command, cwd=cwd, dry_run=False, capture=True)
    return component_id in output


def require_executable(requested: str, *, skip: bool) -> str:
    if skip:
        return requested
    resolved = shutil.which(requested) if "/" not in requested else requested
    if not resolved or not Path(resolved).exists():
        raise RuntimeError(f"Required executable not found: {requested}")
    return str(resolved)


def install_codex(codex: str, repo_root: Path, *, dry_run: bool) -> None:
    data = json_command([codex, "plugin", "marketplace", "list", "--json"], cwd=repo_root, dry_run=dry_run)
    names = {item.get("name") for item in data.get("marketplaces", [])}
    if MARKETPLACE_ID not in names:
        run([codex, "plugin", "marketplace", "add", str(repo_root)], cwd=repo_root, dry_run=dry_run)

    data = json_command([codex, "plugin", "list", "--json"], cwd=repo_root, dry_run=dry_run)
    ids = {item.get("pluginId") for item in data.get("installed", [])}
    selector = f"{PLUGIN_ID}@{MARKETPLACE_ID}"
    if selector not in ids:
        run([codex, "plugin", "add", selector], cwd=repo_root, dry_run=dry_run)


def install_spec_kit(
    specify: str,
    plugin_root: Path,
    project: Path,
    *,
    initialize: bool,
    integration: str,
    dry_run: bool,
) -> None:
    if not project.exists() or not project.is_dir():
        raise RuntimeError(f"Project directory does not exist: {project}")

    if not (project / ".specify").exists():
        if not initialize:
            raise RuntimeError("Project is not initialized with Spec Kit; pass --init-spec-kit")
        run(
            [
                specify,
                "init",
                "--here",
                "--force",
                "--integration",
                integration,
                "--integration-options=--skills",
            ],
            cwd=project,
            dry_run=dry_run,
        )

    preset = plugin_root / "spec-kit" / "preset"
    extension = plugin_root / "spec-kit" / "extension"
    workflow = plugin_root / "spec-kit" / "workflow" / "workflow.yml"
    bundle = plugin_root / "spec-kit" / "bundle"

    if not contains_component([specify, "preset", "list"], PRESET_ID, cwd=project, dry_run=dry_run):
        run([specify, "preset", "add", "--dev", str(preset), "--priority", "5"], cwd=project, dry_run=dry_run)
    if not contains_component([specify, "extension", "list"], EXTENSION_ID, cwd=project, dry_run=dry_run):
        run([specify, "extension", "add", str(extension), "--dev", "--priority", "5"], cwd=project, dry_run=dry_run)
    if not contains_component([specify, "workflow", "list"], WORKFLOW_ID, cwd=project, dry_run=dry_run):
        run([specify, "workflow", "add", str(workflow), "--dev"], cwd=project, dry_run=dry_run)

    run([specify, "bundle", "validate", "--path", str(bundle), "--offline"], cwd=project, dry_run=dry_run)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Target project for Spec Kit components")
    parser.add_argument("--init-spec-kit", action="store_true", help="Initialize the target project when needed")
    parser.add_argument("--integration", default="codex", help="Spec Kit integration used during initialization")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--specify-bin", default="specify")
    parser.add_argument("--skip-codex-plugin", action="store_true")
    parser.add_argument("--skip-spec-kit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plugin_root = Path(__file__).resolve().parents[1]
    repo_root = plugin_root.parents[1]
    project = args.project.resolve()

    try:
        codex = require_executable(args.codex_bin, skip=args.skip_codex_plugin)
        specify = require_executable(args.specify_bin, skip=args.skip_spec_kit)
        if not args.skip_codex_plugin:
            install_codex(codex, repo_root, dry_run=args.dry_run)
        if not args.skip_spec_kit:
            install_spec_kit(
                specify,
                plugin_root,
                project,
                initialize=args.init_spec_kit,
                integration=args.integration,
                dry_run=args.dry_run,
            )
    except (RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"install failed: {exc}", file=sys.stderr)
        return 1

    print("GK Engineering toolkit is installed.")
    if not args.skip_codex_plugin:
        print("Restart Codex to load the plugin skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
