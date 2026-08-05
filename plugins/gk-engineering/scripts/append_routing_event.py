#!/usr/bin/env python3
"""Validate and atomically append one event to model-routing.jsonl."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--event", type=Path, required=True)
    args = parser.parse_args()

    if not args.event.is_file():
        print(f"ERROR: routing event not found: {args.event}", file=sys.stderr)
        return 1
    try:
        event = json.loads(args.event.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: invalid routing event: {error}", file=sys.stderr)
        return 1
    if not isinstance(event, dict):
        print("ERROR: routing event root must be an object", file=sys.stderr)
        return 1

    existing = args.log.read_text(encoding="utf-8") if args.log.is_file() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    candidate = existing + json.dumps(event, separators=(",", ":")) + "\n"
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=args.log.parent,
        prefix=f".{args.log.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(candidate)
        temporary = Path(handle.name)

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "scripts" / "validate_model_routing.py"),
            str(temporary),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        temporary.unlink(missing_ok=True)
        detail = result.stderr.strip() or result.stdout.strip()
        print(detail, file=sys.stderr)
        return 1
    os.replace(temporary, args.log)
    print(f"OK: appended {event.get('turn_id', '<unknown>')} to {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
