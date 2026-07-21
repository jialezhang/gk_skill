#!/usr/bin/env python3
"""Validate structural and approval invariants of an Agent-ready PRD."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    "Product Decision Summary",
    "Product Outcome",
    "Evidence and Current Behavior",
    "Product Invariants",
    "Product Concepts and State Model",
    "Experience and Behavior Rules",
    "Requirements",
    "Non-goals",
    "Core Journeys",
    "Human Decision Boundary",
    "Implementation Freedom",
    "Acceptance Inventory",
    "Success Metrics",
    "Product Assumptions and Open Questions",
    "Rejected Options",
    "Release and Rollback Requirements",
    "Change Control",
    "Completion Definition",
]


def frontmatter(text: str) -> str | None:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    return match.group(1) if match else None


def value(block: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", block)
    return match.group(1).strip().strip('"\'') if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prd", type=Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args()

    if not args.prd.is_file():
        print(f"ERROR: PRD not found: {args.prd}", file=sys.stderr)
        return 1

    text = args.prd.read_text(encoding="utf-8")
    errors: list[str] = []
    block = frontmatter(text)
    if block is None:
        errors.append("missing YAML frontmatter")
    else:
        status = value(block, "prd_status")
        version = value(block, "prd_version")
        if status not in {"DRAFT", "REVIEW_REQUIRED", "APPROVED", "CHANGE_REQUESTED", "SUPERSEDED"}:
            errors.append(f"invalid prd_status: {status!r}")
        if not version or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            errors.append(f"invalid prd_version: {version!r}")
        if status == "APPROVED":
            if value(block, "approved_by") != "user":
                errors.append("APPROVED PRD must have approved_by: user")
            if value(block, "approved_at") in {None, "", "null"}:
                errors.append("APPROVED PRD must have approved_at")

    headings = set(re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    for heading in REQUIRED_HEADINGS:
        if heading not in headings:
            errors.append(f"missing heading: {heading}")

    requirement_ids = re.findall(r"\|\s*(R-\d+)\s*\|", text)
    if not requirement_ids:
        errors.append("no requirement IDs found")
    if len(requirement_ids) != len(set(requirement_ids)):
        errors.append("duplicate requirement IDs")

    journey_ids = re.findall(r"^###\s+(J-\d+):", text, re.MULTILINE)
    if not journey_ids:
        errors.append("no core journey IDs found")
    if len(journey_ids) != len(set(journey_ids)):
        errors.append("duplicate journey IDs")

    if not args.allow_placeholders:
        placeholder_patterns = [r"\[Feature\]", r"\[Journey\]", r"\[Who\]", r"\|\s*R-01\s*\|\s*P0\s*\|\s*\|"]
        for pattern in placeholder_patterns:
            if re.search(pattern, text):
                errors.append(f"unresolved template placeholder: {pattern}")

    if "blocking" not in text.lower() or "real-target" not in text.lower():
        errors.append("acceptance inventory must identify blocking real-target evidence")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.prd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
