#!/usr/bin/env python3
"""Validate a pre-terminal delivery telemetry snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()

    if not args.snapshot.is_file():
        print(f"ERROR: telemetry snapshot not found: {args.snapshot}", file=sys.stderr)
        return 1
    try:
        data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: invalid telemetry snapshot: {error}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("ERROR: telemetry snapshot root must be an object", file=sys.stderr)
        return 1
    snapshot = data.get("completion_snapshot")
    if not isinstance(snapshot, dict):
        print("ERROR: completion_snapshot is required", file=sys.stderr)
        return 1
    errors: list[str] = []
    if snapshot.get("status") not in {"captured", "captured_with_unavailable"}:
        errors.append("completion_snapshot has invalid status")
    if snapshot.get("capture_event") != "before_terminal_transition":
        errors.append("completion_snapshot must be captured before_terminal_transition")
    for key in ("captured_at", "source"):
        if not isinstance(snapshot.get(key), str) or not snapshot.get(key):
            errors.append(f"completion_snapshot requires {key}")
    unavailable = snapshot.get("unavailable_fields")
    if not isinstance(unavailable, list) or not all(isinstance(item, str) for item in unavailable):
        errors.append("completion_snapshot.unavailable_fields must be a string list")
    if snapshot.get("status") == "captured" and unavailable:
        errors.append("captured telemetry cannot declare unavailable fields")
    if snapshot.get("status") == "captured_with_unavailable" and not unavailable:
        errors.append("captured_with_unavailable requires unavailable_fields")
    for key in ("by_model", "by_phase"):
        if not isinstance(data.get(key), dict):
            errors.append(f"telemetry report requires {key}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.snapshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
