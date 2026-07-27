#!/usr/bin/env python3
"""Collect exact-turn elapsed time and token usage from routing logs and rollouts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def rollout_files(thread_id: str, roots: list[Path]) -> list[Path]:
    matches: list[Path] = []
    for root in roots:
        if root.is_dir():
            matches.extend(root.rglob(f"*{thread_id}*.jsonl"))
    return sorted(set(matches))


def subtract_usage(current: dict[str, Any], previous: dict[str, int]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key in TOKEN_FIELDS:
        value = current.get(key)
        now = value if isinstance(value, int) and value >= 0 else 0
        before = previous.get(key, 0)
        result[key] = now - before if now >= before else now
    return result


def read_turns(path: Path) -> dict[str, dict[str, Any]]:
    turns: dict[str, dict[str, Any]] = {}
    current_turn: str | None = None
    previous_total: dict[str, int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        timestamp = parse_time(event.get("timestamp"))
        payload = event.get("payload")
        if event.get("type") == "turn_context" and isinstance(payload, dict):
            turn_id = payload.get("turn_id")
            model = payload.get("model")
            if isinstance(turn_id, str):
                current_turn = turn_id
                entry = turns.setdefault(
                    turn_id,
                    {
                        "observed_model": model,
                        "started_at": timestamp,
                        "ended_at": timestamp,
                        "tokens": {key: 0 for key in TOKEN_FIELDS},
                    },
                )
                if entry.get("observed_model") != model:
                    entry["ambiguous_model"] = True
            continue
        if current_turn and timestamp:
            turns[current_turn]["ended_at"] = timestamp
        if (
            current_turn
            and event.get("type") == "event_msg"
            and isinstance(payload, dict)
            and payload.get("type") == "token_count"
        ):
            info = payload.get("info")
            total = info.get("total_token_usage") if isinstance(info, dict) else None
            if isinstance(total, dict):
                delta = subtract_usage(total, previous_total)
                previous_total = {
                    key: value
                    for key in TOKEN_FIELDS
                    if isinstance((value := total.get(key)), int)
                }
                for key, value in delta.items():
                    turns[current_turn]["tokens"][key] += value
    return turns


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routing_log", type=Path)
    parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument(
        "--archived-root",
        type=Path,
        default=Path.home() / ".codex" / "archived_sessions",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument(
        "--completion-snapshot",
        action="store_true",
        help="mark this report as captured immediately before a terminal Goal transition",
    )
    args = parser.parse_args()

    if not args.routing_log.is_file():
        print(f"ERROR: routing log not found: {args.routing_log}", file=sys.stderr)
        return 1

    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(
        args.routing_log.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as error:
            print(f"ERROR: line {line_number}: invalid JSON: {error.msg}", file=sys.stderr)
            return 1
        if isinstance(record, dict):
            records.append(record)

    roots = [args.sessions_root, args.archived_root]
    cache: dict[Path, dict[str, dict[str, Any]]] = {}
    turns: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for record in records:
        thread_id = record.get("thread_id")
        turn_id = record.get("turn_id")
        if not isinstance(thread_id, str) or not isinstance(turn_id, str):
            continue
        matches: list[tuple[Path, dict[str, Any]]] = []
        for path in rollout_files(thread_id, roots):
            parsed = cache.setdefault(path, read_turns(path))
            if turn_id in parsed:
                matches.append((path, parsed[turn_id]))
        if len(matches) != 1:
            missing.append(
                {
                    "thread_id": thread_id,
                    "turn_id": turn_id,
                    "reason": "not_found" if not matches else "ambiguous_rollout",
                }
            )
            continue
        source, observed = matches[0]
        started = observed.get("started_at")
        ended = observed.get("ended_at")
        elapsed = (
            max(0.0, (ended - started).total_seconds())
            if isinstance(started, datetime) and isinstance(ended, datetime)
            else None
        )
        turns.append(
            {
                "thread_id": thread_id,
                "turn_id": turn_id,
                "phase": record.get("phase"),
                "task_class": record.get("task_class"),
                "requested_model": record.get("requested_model"),
                "observed_model": observed.get("observed_model"),
                "elapsed_seconds": elapsed,
                "tokens": observed.get("tokens"),
                "source": str(source),
            }
        )

    by_model: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"turns": 0, "elapsed_seconds": 0.0, **{key: 0 for key in TOKEN_FIELDS}}
    )
    by_phase: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"turns": 0, "elapsed_seconds": 0.0, **{key: 0 for key in TOKEN_FIELDS}}
    )
    for turn in turns:
        for group, key in (
            (by_model, str(turn.get("observed_model"))),
            (by_phase, str(turn.get("phase"))),
        ):
            bucket = group[key]
            bucket["turns"] += 1
            bucket["elapsed_seconds"] += turn.get("elapsed_seconds") or 0.0
            for token_key in TOKEN_FIELDS:
                bucket[token_key] += (turn.get("tokens") or {}).get(token_key, 0)

    report: dict[str, Any] = {
        "schema_version": "1.1",
        "routing_log": str(args.routing_log),
        "turns": turns,
        "by_model": dict(sorted(by_model.items())),
        "by_phase": dict(sorted(by_phase.items())),
        "missing_turns": missing,
    }
    if args.completion_snapshot:
        unavailable = [
            f"turn:{item['thread_id']}:{item['turn_id']}:{item['reason']}"
            for item in missing
        ]
        report["completion_snapshot"] = {
            "status": "captured_with_unavailable" if unavailable else "captured",
            "capture_event": "before_terminal_transition",
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "runtime_turn_telemetry",
            "unavailable_fields": unavailable,
        }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"OK: wrote {args.output} ({len(turns)} turns, {len(missing)} missing)")
    else:
        print(rendered, end="")
    if args.require_complete and missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
