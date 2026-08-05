#!/usr/bin/env python3
"""Revalidate a completion receipt against its immutable input digests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from delivery_contract import file_digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()

    if not args.receipt.is_file():
        print(f"ERROR: completion receipt not found: {args.receipt}", file=sys.stderr)
        return 1
    try:
        data = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: invalid completion receipt: {error}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("ERROR: completion receipt root must be an object", file=sys.stderr)
        return 1

    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("unsupported completion receipt schema_version")
    if data.get("status") != "ready":
        errors.append("completion receipt status must be ready")
    for key in ("candidate_commit", "issued_at"):
        if not isinstance(data.get(key), str) or not data.get(key):
            errors.append(f"completion receipt requires {key}")
    inputs = data.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        errors.append("completion receipt inputs must be a non-empty object")
        inputs = {}
    for label, item in inputs.items():
        if not isinstance(item, dict):
            errors.append(f"completion receipt input {label} must be an object")
            continue
        raw_path, expected = item.get("path"), item.get("sha256")
        if not isinstance(raw_path, str) or not raw_path or not isinstance(expected, str):
            errors.append(f"completion receipt input {label} is incomplete")
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            path = args.receipt.parent / path
        if not path.is_file():
            errors.append(f"completion receipt input missing: {label}={path}")
            continue
        mode = item.get("digest_mode", "raw")
        try:
            actual = file_digest(path, str(mode))
        except ValueError as error:
            errors.append(f"completion receipt input {label}: {error}")
            continue
        if actual != expected:
            errors.append(
                f"COMPLETION_RECEIPT_INPUT_CHANGED {label} expected={expected} actual={actual}"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
