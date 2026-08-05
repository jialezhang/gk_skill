#!/usr/bin/env python3
"""Validate approval, traceability, IDs, and dependency integrity of plan artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_contract import EXTERNAL_EFFECT_POLICIES  # noqa: E402


PLAN_HEADINGS = {
    "Product Outcome and Approved Scope",
    "Requirement Traceability",
    "Target Identity",
    "Current-State Evidence",
    "Change Classification",
    "Commitment Ledger",
    "Assumption Ledger",
    "Responsibility Replacement",
    "Data, Identity, and Safety Flow",
    "Runtime Lifecycle and State Convergence",
    "阶段真实用户旅程",
    "Complete Milestone Baseline",
    "Dependency Graph",
    "Delegation Map",
    "Verification Strategy",
    "Plan Review Record",
    "Rollout, Rollback, and Legacy",
    "Plan Revision Protocol",
    "Remaining Risks",
    "Approval Checklist",
}

VERIFICATION_HEADINGS = {
    "Target Identity",
    "Automated and Integration Matrix",
    "Runtime Lifecycle and Convergence Matrix",
    "Exact-target Acceptance Cases",
    "Execution Scenario Coverage",
    "Candidate Evidence Policy",
    "Gate Matrix",
    "Final Reconciliation",
}


def read(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"missing artifact: {path}")
    return path.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^([a-zA-Z0-9_]+):\s*(.*?)\s*$", line)
        if item:
            values[item.group(1)] = item.group(2).strip().strip('"\'')
    return values


def task_dependencies(tasks_text: str) -> tuple[set[str], dict[str, set[str]]]:
    matches = list(re.finditer(r"^##\s+\[(T-\d+)\]\s+.*$", tasks_text, re.MULTILINE))
    task_ids = {match.group(1) for match in matches}
    dependencies: dict[str, set[str]] = defaultdict(set)
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(tasks_text)
        body = tasks_text[match.end():end]
        dep_line = re.search(r"^\- \*\*Dependencies\*\*:\s*(.*?)\s*$", body, re.MULTILINE)
        if dep_line and dep_line.group(1).lower() != "none":
            dependencies[match.group(1)].update(re.findall(r"T-\d+", dep_line.group(1)))
    return task_ids, dependencies


def task_blocks(tasks_text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^##\s+\[(T-\d+)\]\s+.*$", tasks_text, re.MULTILINE))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(tasks_text)
        blocks.append((match.group(1), tasks_text[match.end():end]))
    return blocks


def field(body: str, name: str) -> str | None:
    match = re.search(
        rf"^\s*-\s+(?:\*\*)?{re.escape(name)}(?:\*\*)?:\s*(.*?)\s*$",
        body,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def scenario_blocks(verification: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^###\s+(SC-\d+):.*$", verification, re.MULTILINE))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(verification)
        blocks.append((match.group(1), verification[match.end():end]))
    return blocks


def find_cycle(task_ids: set[str], dependencies: dict[str, set[str]]) -> bool:
    outgoing: dict[str, set[str]] = defaultdict(set)
    indegree = {task: 0 for task in task_ids}
    for task, deps in dependencies.items():
        for dep in deps:
            if dep in task_ids:
                outgoing[dep].add(task)
                indegree[task] += 1
    queue = deque(task for task, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        task = queue.popleft()
        visited += 1
        for child in outgoing[task]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    return visited != len(task_ids)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prd", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    try:
        prd = read(args.prd)
        plan = read(args.plan)
        tasks = read(args.tasks)
        verification = read(args.verification)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    prd_meta, plan_meta = frontmatter(prd), frontmatter(plan)
    tasks_meta, verification_meta = frontmatter(tasks), frontmatter(verification)
    if prd_meta.get("prd_status") != "APPROVED":
        errors.append("PRD must be APPROVED")
    if plan_meta.get("plan_status") not in {"PLAN_DRAFT", "PLAN_REVIEW_REQUIRED", "PLAN_APPROVED"}:
        errors.append("invalid plan_status")
    if tasks_meta.get("tasks_status") != plan_meta.get("plan_status"):
        errors.append("tasks_status must match plan_status")
    if verification_meta.get("verification_status") != plan_meta.get("plan_status"):
        errors.append("verification_status must match plan_status")
    if plan_meta.get("prd_version") != prd_meta.get("prd_version"):
        errors.append("plan prd_version does not match PRD")
    if tasks_meta.get("plan_version") != plan_meta.get("plan_version"):
        errors.append("tasks plan_version does not match plan")
    if verification_meta.get("plan_version") != plan_meta.get("plan_version"):
        errors.append("verification plan_version does not match plan")

    headings = set(re.findall(r"^##\s+(.+?)\s*$", plan, re.MULTILINE))
    for heading in sorted(PLAN_HEADINGS - headings):
        errors.append(f"plan missing heading: {heading}")

    verification_headings = set(re.findall(r"^##\s+(.+?)\s*$", verification, re.MULTILINE))
    for heading in sorted(VERIFICATION_HEADINGS - verification_headings):
        errors.append(f"verification missing heading: {heading}")

    requirement_rows = re.findall(r"\|\s*(R-\d+)\s*\|\s*(P[01])\s*\|", prd)
    requirements = {req for req, _priority in requirement_rows}
    if not requirements:
        errors.append("no P0/P1 requirement rows found in PRD")
    for requirement in sorted(requirements):
        if requirement not in tasks:
            errors.append(f"requirement missing from tasks: {requirement}")
        if requirement not in verification:
            errors.append(f"requirement missing from verification: {requirement}")

    task_ids, dependencies = task_dependencies(tasks)
    if not task_ids:
        errors.append("no task IDs found")
    for task, deps in dependencies.items():
        unknown = deps - task_ids
        for dep in sorted(unknown):
            errors.append(f"{task} depends on unknown task {dep}")
        if task in deps:
            errors.append(f"{task} depends on itself")
    if task_ids and find_cycle(task_ids, dependencies):
        errors.append("task dependency graph contains a cycle")
    for task_id, body in task_blocks(tasks):
        test_level = field(body, "test_level")
        effect_policy = field(body, "External effect policy")
        invalidation_keys = field(body, "evidence invalidation keys")
        if test_level not in {"fast", "change", "full"}:
            errors.append(f"{task_id}: invalid or missing test_level")
        if effect_policy not in EXTERNAL_EFFECT_POLICIES:
            errors.append(f"{task_id}: invalid or missing External effect policy")
        if not invalidation_keys:
            errors.append(f"{task_id}: evidence invalidation keys are required")
        if test_level == "full":
            reason = field(body, "full-run reason")
            if not reason or reason.lower() in {"not_applicable", "none", "n/a"}:
                errors.append(f"{task_id}: full test level requires a full-run reason")
        if effect_policy == "authorized":
            budget = field(body, "External effect authorization/budget")
            if not budget or budget.lower() in {"not_applicable", "none", "n/a"}:
                errors.append(f"{task_id}: authorized external effect requires authorization/budget")

    gates = set(re.findall(r"^###\s+\[(G-\d+)\]", tasks, re.MULTILINE))
    if not gates:
        errors.append("no gate IDs found")
    acceptance_cases = set(re.findall(r"^###\s+(AC-\d+):", verification, re.MULTILINE))
    if not acceptance_cases:
        errors.append("no exact-target acceptance cases found")
    scenarios = scenario_blocks(verification)
    if not scenarios:
        errors.append("no execution scenarios found")
    covered_claims: set[str] = set()
    for scenario_id, body in scenarios:
        proves = field(body, "Proves")
        referenced_claims = set(re.findall(r"AC-\d+", proves or ""))
        if not referenced_claims:
            errors.append(f"{scenario_id}: Proves must reference at least one AC")
        for claim in sorted(referenced_claims - acceptance_cases):
            errors.append(f"{scenario_id}: references unknown acceptance claim {claim}")
        covered_claims.update(referenced_claims)
        effect_policy = field(body, "External effect policy")
        if effect_policy not in EXTERNAL_EFFECT_POLICIES:
            errors.append(f"{scenario_id}: invalid or missing External effect policy")
        if effect_policy == "authorized":
            budget = field(body, "External effect authorization/budget")
            if not budget or budget.lower() in {"not_applicable", "none", "n/a"}:
                errors.append(f"{scenario_id}: authorized external effect requires authorization/budget")
        matrix_type = field(body, "Matrix type")
        if matrix_type not in {"representative", "pairwise", "cartesian"}:
            errors.append(f"{scenario_id}: invalid or missing Matrix type")
        if matrix_type == "cartesian":
            for required_field in (
                "Interaction risk",
                "Pairwise insufficient because",
                "Estimated executions",
                "Budget",
            ):
                value = field(body, required_field)
                if not value or value.lower() in {"not_applicable", "none", "n/a"}:
                    errors.append(
                        f"{scenario_id}: cartesian matrix requires {required_field}"
                    )
    for claim in sorted(acceptance_cases - covered_claims):
        errors.append(f"acceptance claim has no execution scenario: {claim}")

    if not args.allow_placeholders:
        for text, label in ((plan, "plan"), (tasks, "tasks"), (verification, "verification")):
            if re.search(r"\[(?:Feature|FEATURE|Observable outcome|Gate name|Blocking journey)\]", text):
                errors.append(f"{label} contains unresolved placeholders")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: plan artifacts are structurally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
