#!/usr/bin/env python3
"""Behavioral tests for proactive Terra subagent routing hooks."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOK = PLUGIN_ROOT / "hooks" / "terra_route_guard.py"


def run_hook(payload: dict[str, object], state_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SOL_TERRA_ROUTE_GUARD_STATE"] = str(state_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def hook_output(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(result.stdout) if result.stdout.strip() else {}


def spawn_payload(**tool_input: object) -> dict[str, object]:
    return {
        "session_id": "session-1",
        "turn_id": "parent-turn-1",
        "hook_event_name": "PreToolUse",
        "permission_mode": "bypassPermissions",
        "model": "gpt-5.6-sol",
        "tool_name": "Agent",
        "tool_use_id": "spawn-call-1",
        "tool_input": {
            "task_name": "terra_implementation",
            "fork_turns": "none",
            "model": "gpt-5.6-terra",
            "message": "route_class: terra_implementation\nROUTING HANDSHAKE ONLY",
            **tool_input,
        },
    }


class TerraRouteGuardTests(unittest.TestCase):
    def test_non_implementation_subagent_is_not_intercepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(
                {
                    **spawn_payload(),
                    "tool_input": {
                        "task_name": "read_only_explorer",
                        "agent_type": "explore",
                        "message": "Inspect the repository without editing.",
                    },
                },
                Path(tmp) / "state.sqlite",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_implementation_spawn_requires_explicit_terra_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = spawn_payload()
            tool_input = payload["tool_input"]
            self.assertIsInstance(tool_input, dict)
            assert isinstance(tool_input, dict)
            tool_input.pop("model")
            result = run_hook(payload, Path(tmp) / "state.sqlite")
        output = hook_output(result)
        self.assertEqual(
            output["hookSpecificOutput"]["permissionDecision"],  # type: ignore[index]
            "deny",
        )
        self.assertIn("TERRA_MODEL_REQUIRED", json.dumps(output))
        self.assertIn("CONTINUE_WITH_CURRENT_MODEL", json.dumps(output))
        self.assertIn("THREE_TERRA_ATTEMPTS", json.dumps(output))

    def test_implementation_spawn_rejects_conflicting_agent_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(
                spawn_payload(agent_type="team-executor"),
                Path(tmp) / "state.sqlite",
            )
        output = hook_output(result)
        self.assertEqual(
            output["hookSpecificOutput"]["permissionDecision"],  # type: ignore[index]
            "deny",
        )
        self.assertIn("TERRA_AGENT_TYPE_CONFLICT", json.dumps(output))

    def test_implementation_spawn_requires_limited_fork_and_handshake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            bad_fork = run_hook(spawn_payload(fork_turns="all"), state)
            bad_message = run_hook(
                spawn_payload(message="route_class: terra_implementation\nImplement now."),
                state,
            )
        self.assertIn("TERRA_FORK_TURNS_REQUIRED", json.dumps(hook_output(bad_fork)))
        self.assertIn("TERRA_HANDSHAKE_REQUIRED", json.dumps(hook_output(bad_message)))

    def test_only_one_terra_switch_can_be_pending_per_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            first = run_hook(spawn_payload(), state)
            second_payload = spawn_payload()
            second_payload["tool_use_id"] = "spawn-call-2"
            second = run_hook(second_payload, state)
        self.assertIn("SOL_TERRA_ROUTE_PENDING", json.dumps(hook_output(first)))
        self.assertIn("TERRA_ROUTE_ALREADY_PENDING", json.dumps(hook_output(second)))
        self.assertIn("CONTINUE_WITH_CURRENT_MODEL", json.dumps(hook_output(second)))

    def test_expired_pending_route_does_not_block_a_later_switch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            run_hook(spawn_payload(), state)
            with sqlite3.connect(state) as connection:
                connection.execute(
                    "UPDATE pending_routes SET created_at = '2000-01-01T00:00:00+00:00'"
                )
            second_payload = spawn_payload()
            second_payload["tool_use_id"] = "spawn-call-2"
            second = run_hook(second_payload, state)
            with sqlite3.connect(state) as connection:
                statuses = [
                    row[0]
                    for row in connection.execute(
                        "SELECT status FROM pending_routes ORDER BY id"
                    )
                ]
        self.assertIn("SOL_TERRA_ROUTE_PENDING", json.dumps(hook_output(second)))
        self.assertEqual(statuses, ["expired", "pending"])

    def test_non_default_subagent_does_not_consume_pending_terra_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            run_hook(spawn_payload(), state)
            explorer = run_hook(
                {
                    "session_id": "session-1",
                    "turn_id": "explore-turn-1",
                    "hook_event_name": "SubagentStart",
                    "permission_mode": "bypassPermissions",
                    "model": "gpt-5.3-codex-spark",
                    "agent_id": "agent-explore-1",
                    "agent_type": "explore",
                },
                state,
            )
            terra = run_hook(
                {
                    "session_id": "session-1",
                    "turn_id": "terra-turn-1",
                    "hook_event_name": "SubagentStart",
                    "permission_mode": "bypassPermissions",
                    "model": "gpt-5.6-terra",
                    "agent_id": "agent-terra-1",
                    "agent_type": "default",
                },
                state,
            )
        self.assertEqual(explorer.stdout, "")
        self.assertIn("SOL_TERRA_ROUTE_VERIFIED", json.dumps(hook_output(terra)))

    def test_valid_spawn_and_start_verify_model_and_inherited_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            spawn = run_hook(spawn_payload(), state)
            spawn_context = (
                hook_output(spawn)["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
            )
            self.assertIn("SOL_TERRA_ROUTE_PENDING", spawn_context)
            nonce = str(spawn_context).split("nonce=", 1)[1].split()[0]

            start = run_hook(
                {
                    "session_id": "session-1",
                    "turn_id": "terra-turn-1",
                    "hook_event_name": "SubagentStart",
                    "permission_mode": "bypassPermissions",
                    "model": "gpt-5.6-terra",
                    "agent_id": "agent-terra-1",
                    "agent_type": "default",
                },
                state,
            )
            start_context = (
                hook_output(start)["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
            )
        self.assertIn("SOL_TERRA_ROUTE_VERIFIED", start_context)
        self.assertIn(f"nonce={nonce}", start_context)
        self.assertIn("permission_mode=bypassPermissions", start_context)

    def test_start_quarantines_model_or_permission_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            run_hook(spawn_payload(), state)
            start = run_hook(
                {
                    "session_id": "session-1",
                    "turn_id": "wrong-turn",
                    "hook_event_name": "SubagentStart",
                    "permission_mode": "default",
                    "model": "gpt-5.4",
                    "agent_id": "agent-wrong",
                    "agent_type": "team-executor",
                },
                state,
            )
            start_context = (
                hook_output(start)["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
            )
        self.assertIn("SOL_TERRA_ROUTE_MISMATCH", start_context)
        self.assertIn("MODEL_ROUTE_MISMATCH", start_context)
        self.assertIn("PERMISSION_INHERITANCE_MISMATCH", start_context)
        self.assertIn("do not use tools", start_context)
        self.assertIn("CONTINUE_WITH_CURRENT_MODEL", start_context)
        self.assertIn("THREE_TERRA_ATTEMPTS", start_context)

    def test_subagent_start_hook_error_returns_a_fallback_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(
                {
                    "session_id": "session-1",
                    "turn_id": "terra-turn-1",
                    "hook_event_name": "SubagentStart",
                    "permission_mode": "bypassPermissions",
                    "model": "gpt-5.6-terra",
                    "agent_id": "agent-terra-1",
                    "agent_type": "default",
                },
                Path(tmp),
            )
        output = hook_output(result)["hookSpecificOutput"]  # type: ignore[index]
        self.assertEqual(output["hookEventName"], "SubagentStart")  # type: ignore[index]
        self.assertIn("SOL_TERRA_ROUTE_GUARD_ERROR", json.dumps(output))
        self.assertIn("CONTINUE_WITH_CURRENT_MODEL", json.dumps(output))


if __name__ == "__main__":
    unittest.main()
