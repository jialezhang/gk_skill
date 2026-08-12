#!/usr/bin/env python3
"""Atomically recover an empty routing log from raw-runtime-verifiable records."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def load_records(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    records: list[dict[str, object]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return records, [f"recovery source: {error}"]
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(
                f"recovery source line {line_number}: invalid JSON: {error.msg}"
            )
            continue
        if not isinstance(value, dict):
            errors.append(
                f"recovery source line {line_number}: record must be an object"
            )
            continue
        records.append(value)
    if not records:
        errors.append("ROUTING_RECOVERY_SOURCE_EMPTY")
    return records, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="JSONL records reconstructed from durable routing-event evidence.",
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=Path.home() / ".codex" / "sessions",
    )
    parser.add_argument(
        "--archived-root",
        type=Path,
        default=Path.home() / ".codex" / "archived_sessions",
    )
    parser.add_argument(
        "--completion-ready",
        action="store_true",
        help="Also require the Canary, transition Canary, and execution handshake set.",
    )
    args = parser.parse_args()

    if args.log.exists() and not args.log.is_file():
        print(
            f"ERROR: ROUTING_RECOVERY_LOG_NOT_REGULAR_FILE: {args.log}",
            file=sys.stderr,
        )
        return 1
    if args.log.is_file():
        try:
            existing = args.log.read_text(encoding="utf-8")
        except OSError as error:
            print(f"ERROR: routing log: {error}", file=sys.stderr)
            return 1
        if existing.strip():
            print(
                "ERROR: ROUTING_RECOVERY_REQUIRES_EMPTY_LOG; "
                "append new events with append_routing_event.py",
                file=sys.stderr,
            )
            return 1

    records, errors = load_records(args.source)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    args.log.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=args.log.parent,
        prefix=f".{args.log.name}.recovery.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        for record in records:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        temporary = Path(handle.name)

    command = [
        sys.executable,
        str(PLUGIN_ROOT / "scripts" / "validate_model_routing.py"),
        str(temporary),
        "--require-runtime-evidence",
        "--sessions-root",
        str(args.sessions_root),
        "--archived-root",
        str(args.archived_root),
    ]
    if args.completion_ready:
        command.extend(
            [
                "--require-canary",
                "--require-transition-canary",
                "--require-handshake",
            ]
        )
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        temporary.unlink(missing_ok=True)
        detail = result.stderr.strip() or result.stdout.strip() or "validator failed"
        print("ERROR: ROUTING_RECOVERY_RAW_EVIDENCE_REQUIRED", file=sys.stderr)
        print(detail, file=sys.stderr)
        return 1

    try:
        os.replace(temporary, args.log)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        print(f"ERROR: routing log replacement failed: {error}", file=sys.stderr)
        return 1
    print(f"OK: recovered {len(records)} routing records into {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
