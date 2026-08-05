#!/usr/bin/env python3
"""Canonical, project-agnostic delivery contract constants."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


DELIVERY_STATUSES = {
    "DELIVERY_ACTIVE",
    "GATE_REVIEW",
    "PLAN_CONFLICT",
    "PRODUCT_DECISION_REQUIRED",
    "VERIFICATION_BLOCKED",
    "TARGET_VERIFIED",
    "GOAL_TARGET_VERIFIED",
    "COMPLETE",
    "BLOCKED",
}

DELIVERY_VERIFIED_STATUSES = {"TARGET_VERIFIED", "GOAL_TARGET_VERIFIED", "COMPLETE"}

PROGRAM_STATUSES = {
    "PROGRAM_ACTIVE",
    "PROGRAM_GATE_REVIEW",
    "PROGRAM_INTEGRATION_PENDING",
    "PROGRAM_TARGET_VERIFIED",
    "COMPLETE",
    "BLOCKED",
}

PROGRAM_VERIFIED_STATUSES = {"PROGRAM_TARGET_VERIFIED", "COMPLETE"}
GOAL_TERMINAL_STATUSES = {"GOAL_TARGET_VERIFIED", "EXPLICITLY_DEFERRED"}
COMPLETION_SCOPES = {"branch", "merged", "deployed", "production_verified"}

EVIDENCE_STATUSES = {"draft", "candidate", "accepted", "invalidated", "superseded"}
PROVENANCE_STATUSES = {"pending", "verified", "not_applicable", "invalidated"}
EXTERNAL_EFFECT_POLICIES = {"forbidden", "sandboxed", "authorized", "not_applicable"}
LEGACY_PROVIDER_MODES = {
    "mock",
    "sandbox",
    "real_free",
    "real_expensive",
    "not_applicable",
}


def version_at_least(value: object, required: tuple[int, int]) -> bool:
    """Compare major/minor versions without adding a packaging dependency."""
    if not isinstance(value, str):
        return False
    try:
        parts = tuple(int(part) for part in value.split(".")[:2])
    except ValueError:
        return False
    return parts >= required


def file_digest(path: Path, mode: str = "raw") -> str:
    """Hash an input, optionally ignoring fields changed only by completion commit."""
    if mode == "raw":
        payload = path.read_bytes()
    elif mode == "terminal_state":
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"^status:\s*[A-Z_]+\s*$",
            "status: <terminal-transition>",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        runtime_goal = re.search(
            r"(?ms)^runtime_goal:\s*\n(.*?)(?=^[a-zA-Z0-9_]+:|\Z)", text
        )
        if runtime_goal:
            normalized = re.sub(
                r"^\s{2}status:\s*[a-z_]+\s*$",
                "  status: <terminal-transition>",
                runtime_goal.group(0),
                count=1,
                flags=re.MULTILINE,
            )
            text = text[: runtime_goal.start()] + normalized + text[runtime_goal.end() :]
        text = re.sub(
            r"(?ms)^completion_receipt:\s*\n.*?(?=^[a-zA-Z0-9_]+:|\Z)",
            "completion_receipt: <terminal-transition>\n",
            text,
        )
        payload = text.encode("utf-8")
    else:
        raise ValueError(f"unsupported digest mode: {mode}")
    return hashlib.sha256(payload).hexdigest()
