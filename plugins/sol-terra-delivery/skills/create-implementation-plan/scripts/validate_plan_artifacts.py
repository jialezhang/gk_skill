#!/usr/bin/env python3
"""Validate approval, traceability, IDs, and dependency integrity of plan artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict, deque
from pathlib import Path


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
    "First Realistic Vertical Slice",
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

    gates = set(re.findall(r"^###\s+\[(G-\d+)\]", tasks, re.MULTILINE))
    if not gates:
        errors.append("no gate IDs found")
    acceptance_cases = set(re.findall(r"^###\s+(AC-\d+):", verification, re.MULTILINE))
    if not acceptance_cases:
        errors.append("no exact-target acceptance cases found")

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
