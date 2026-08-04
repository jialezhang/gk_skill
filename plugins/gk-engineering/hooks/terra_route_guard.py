#!/usr/bin/env python3
"""Guard delegated implementation routing without restricting the main agent."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


TERRA_MODEL = "gpt-5.6-terra"
NATIVE_AGENT_TOOL_NAMES = {"Agent", "spawn_agent", "collaboration.spawn_agent"}
ROUTE_CLASS_MARKER = "route_class: terra_implementation"
HANDSHAKE_MARKER = "ROUTING HANDSHAKE ONLY"
PENDING_TTL_SECONDS = 60
IMPLEMENTATION_AGENT_TYPES = {
    "build-fixer",
    "code-simplifier",
    "debugger",
    "executor",
    "team-executor",
    "worker",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_path() -> Path:
    explicit = os.environ.get("SOL_TERRA_ROUTE_GUARD_STATE")
    if explicit:
        return Path(explicit)
    plugin_data = os.environ.get("PLUGIN_DATA")
    if not plugin_data:
        raise RuntimeError("PLUGIN_DATA is required for the Sol Terra route guard")
    return Path(plugin_data) / "terra-route-guard.sqlite"


def connect() -> sqlite3.Connection:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_routes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id TEXT NOT NULL,
          nonce TEXT NOT NULL UNIQUE,
          spawn_tool_use_id TEXT NOT NULL,
          expected_model TEXT NOT NULL,
          expected_permission_mode TEXT NOT NULL,
          status TEXT NOT NULL,
          agent_id TEXT,
          agent_type TEXT,
          start_turn_id TEXT,
          observed_model TEXT,
          observed_permission_mode TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
    )
    cutoff = (
        datetime.now(timezone.utc) - timedelta(seconds=PENDING_TTL_SECONDS)
    ).isoformat()
    connection.execute(
        """
        UPDATE pending_routes
        SET status = 'expired', updated_at = ?
        WHERE status = 'pending' AND created_at < ?
        """,
        (now(), cutoff),
    )
    connection.commit()
    return connection


def emit(value: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(value, separators=(",", ":")))


def additional_context(message: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": message,
        }
    }


def deny(reason: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{reason}. THREE_TERRA_ATTEMPTS: retry the Terra switch until three "
                "total attempts have failed. CONTINUE_WITH_CURRENT_MODEL only after "
                "the third failure; then continue in the parent context using its "
                "current model and record all three attempts in terra_route_fallback."
            ),
        }
    }


def hook_error(event: object, error: Exception) -> dict[str, object]:
    reason = f"SOL_TERRA_ROUTE_GUARD_ERROR: {type(error).__name__}: {error}"
    if event == "PreToolUse":
        return deny(reason)
    return {
        "hookSpecificOutput": {
            "hookEventName": str(event or "SubagentStart"),
            "additionalContext": (
                f"{reason}. THREE_TERRA_ATTEMPTS: discard this unverified context and "
                "retry the Terra switch until three total attempts have failed. "
                "CONTINUE_WITH_CURRENT_MODEL only after the third failure."
            ),
        }
    }


def implementation_route(tool_input: dict[str, Any]) -> bool:
    message = str(tool_input.get("message") or "")
    task_name = str(tool_input.get("task_name") or "")
    agent_type = str(tool_input.get("agent_type") or "")
    return (
        ROUTE_CLASS_MARKER in message
        or task_name.startswith("terra_")
        or agent_type in IMPLEMENTATION_AGENT_TYPES
    )


def valid_fork_turns(value: object) -> bool:
    return value == "none" or (
        isinstance(value, str) and value.isdigit() and int(value) > 0
    )


def handle_pre_tool_use(payload: dict[str, Any]) -> None:
    if payload.get("tool_name") not in NATIVE_AGENT_TOOL_NAMES:
        return
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or not implementation_route(tool_input):
        return

    if tool_input.get("model") != TERRA_MODEL:
        emit(deny("TERRA_MODEL_REQUIRED: delegated implementation must explicitly request gpt-5.6-terra"))
        return
    if not valid_fork_turns(tool_input.get("fork_turns")):
        emit(deny("TERRA_FORK_TURNS_REQUIRED: use fork_turns=\"none\" or a positive limited history"))
        return
    if tool_input.get("agent_type"):
        emit(
            deny(
                "TERRA_AGENT_TYPE_CONFLICT: omit agent_type because a role profile can override "
                "the explicit Terra model"
            )
        )
        return
    message = str(tool_input.get("message") or "")
    if ROUTE_CLASS_MARKER not in message or HANDSHAKE_MARKER not in message:
        emit(
            deny(
                "TERRA_HANDSHAKE_REQUIRED: the first turn must declare "
                "route_class: terra_implementation and ROUTING HANDSHAKE ONLY"
            )
        )
        return

    session_id = str(payload.get("session_id") or "")
    permission_mode = str(payload.get("permission_mode") or "")
    tool_use_id = str(payload.get("tool_use_id") or "")
    nonce = secrets.token_hex(12)
    timestamp = now()
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        pending = connection.execute(
            """
            SELECT nonce
            FROM pending_routes
            WHERE session_id = ? AND status = 'pending'
            ORDER BY id ASC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
        if pending is not None:
            emit(
                deny(
                    "TERRA_ROUTE_ALREADY_PENDING: only one Terra switch may be pending "
                    f"per session (nonce={pending[0]})"
                )
            )
            return
        connection.execute(
            """
            INSERT INTO pending_routes (
              session_id, nonce, spawn_tool_use_id, expected_model,
              expected_permission_mode, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                session_id,
                nonce,
                tool_use_id,
                TERRA_MODEL,
                permission_mode,
                timestamp,
                timestamp,
            ),
        )
    emit(
        additional_context(
            "SOL_TERRA_ROUTE_PENDING "
            f"nonce={nonce} expected_model={TERRA_MODEL} "
            f"expected_permission_mode={permission_mode}. "
            "Do not send the execution packet until the subagent echoes the matching "
            "SOL_TERRA_ROUTE_VERIFIED nonce."
        )
    )


def handle_subagent_start(payload: dict[str, Any]) -> None:
    agent_type = str(payload.get("agent_type") or "")
    if agent_type not in {"", "default"} and agent_type not in IMPLEMENTATION_AGENT_TYPES:
        return
    session_id = str(payload.get("session_id") or "")
    with connect() as connection:
        pending = connection.execute(
            """
            SELECT id, nonce, expected_model, expected_permission_mode
            FROM pending_routes
            WHERE session_id = ? AND status = 'pending'
            ORDER BY id ASC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
        if pending is None:
            return

        row_id, nonce, expected_model, expected_permission_mode = pending
        observed_model = str(payload.get("model") or "")
        observed_permission_mode = str(payload.get("permission_mode") or "")
        errors: list[str] = []
        if observed_model != expected_model:
            errors.append(
                f"MODEL_ROUTE_MISMATCH expected={expected_model} observed={observed_model}"
            )
        if observed_permission_mode != expected_permission_mode:
            errors.append(
                "PERMISSION_INHERITANCE_MISMATCH "
                f"expected={expected_permission_mode} observed={observed_permission_mode}"
            )
        status = "mismatch" if errors else "verified"
        connection.execute(
            """
            UPDATE pending_routes
            SET status = ?, agent_id = ?, agent_type = ?, start_turn_id = ?,
                observed_model = ?, observed_permission_mode = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                str(payload.get("agent_id") or ""),
                agent_type,
                str(payload.get("turn_id") or ""),
                observed_model,
                observed_permission_mode,
                now(),
                row_id,
            ),
        )

    if errors:
        message = (
            f"SOL_TERRA_ROUTE_MISMATCH nonce={nonce} {'; '.join(errors)}. "
            "This context is quarantined: do not use tools, do not edit files, and return "
            "the mismatch to the parent. THREE_TERRA_ATTEMPTS: discard this context and "
            "retry the Terra switch until three total attempts have failed. "
            "CONTINUE_WITH_CURRENT_MODEL only after the third failure."
        )
    else:
        message = (
            f"SOL_TERRA_ROUTE_VERIFIED nonce={nonce} model={observed_model} "
            f"permission_mode={observed_permission_mode}. "
            "This first turn remains handshake-only. Echo this exact verification line to "
            "the parent and wait for a follow-up execution packet."
        )
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": message,
            }
        }
    )


def handle_subagent_stop(payload: dict[str, Any]) -> None:
    agent_id = str(payload.get("agent_id") or "")
    if not agent_id:
        return
    with connect() as connection:
        connection.execute(
            """
            UPDATE pending_routes
            SET status = CASE WHEN status = 'verified' THEN 'stopped' ELSE status END,
                updated_at = ?
            WHERE agent_id = ?
            """,
            (now(), agent_id),
        )


def main() -> int:
    event: object = ""
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("hook input must be an object")
        event = payload.get("hook_event_name")
        if event == "PreToolUse":
            handle_pre_tool_use(payload)
        elif event == "SubagentStart":
            handle_subagent_start(payload)
        elif event == "SubagentStop":
            handle_subagent_stop(payload)
        return 0
    except Exception as error:
        emit(hook_error(event, error))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
