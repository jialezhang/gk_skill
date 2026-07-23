#!/usr/bin/env python3
"""Behavioral tests for Program lifecycle, routing handshake, and candidate evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def run_script(relative: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / relative), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def routing_record(
    turn_id: str,
    task_class: str,
    model: str,
    **extra: object,
) -> dict[str, object]:
    record: dict[str, object] = {
        "thread_id": "thread-1",
        "turn_id": turn_id,
        "task_class": task_class,
        "requested_model": model,
        "request_explicit": True,
        "observed_model": model,
        "observed_source": "rollout.turn_context.payload.model",
        "phase": "execution",
        "verified": True,
        "allowed_reason": "routing_canary" if task_class == "routing_handshake" else task_class,
    }
    record.update(extra)
    return record


class ModelHandshakeTests(unittest.TestCase):
    def validate(self, records: list[dict[str, object]], *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "routing.jsonl"
            path.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            return run_script("scripts/validate_model_routing.py", str(path), *args)

    def test_verified_read_only_handshake_allows_execution(self) -> None:
        handshake = routing_record(
            "handshake-1",
            "routing_handshake",
            "gpt-5.6-terra",
            phase="handshake",
            write_allowed=False,
        )
        execution = routing_record(
            "implementation-1",
            "implementation",
            "gpt-5.6-terra",
            handshake_turn_id="handshake-1",
        )
        result = self.validate([handshake, execution], "--require-handshake")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_execution_without_handshake_is_rejected(self) -> None:
        result = self.validate(
            [routing_record("implementation-1", "implementation", "gpt-5.6-terra")],
            "--require-handshake",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_HANDSHAKE_REQUIRED", result.stderr)

    def test_luna_cannot_run_browser_acceptance(self) -> None:
        result = self.validate(
            [routing_record("browser-1", "browser_e2e", "gpt-5.6-luna")]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("browser_e2e must request gpt-5.6-terra", result.stderr)

    def test_final_acceptance_requires_separate_terra_thread(self) -> None:
        record = routing_record(
            "final-1",
            "final_target_acceptance",
            "gpt-5.6-terra",
            implementation_thread_ids=["thread-1"],
            independence_verified=True,
        )
        result = self.validate([record])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FINAL_ACCEPTANCE_NOT_INDEPENDENT", result.stderr)


class ProgramLifecycleTests(unittest.TestCase):
    @staticmethod
    def complete_state(goal_status: str = "GOAL_TARGET_VERIFIED") -> str:
        return f"""\
schema_version: "1.0"
program_id: "program-1"
status: COMPLETE
completion_scope: branch
runtime_goal:
  created: true
  goal_id: "runtime-1"
  objective: "deliver program"
  status: complete
superseded_runtime_goals: []
controller:
  thread_id: "controller-1"
  lease_updated_at: "2026-07-23T00:00:00Z"
goals:
  - goal_id: "goal-1"
    status: {goal_status}
progress:
  implementation_completed: 1
  implementation_total: 1
  automation_completed: 1
  automation_total: 1
  exact_target_completed: 1
  exact_target_total: 1
  release_completed: 1
  release_total: 1
  current_activity: "complete"
  remaining_p50_minutes: 0
  remaining_p80_minutes: 0
  last_progress_at: "2026-07-23T00:00:00Z"
release:
  integration_status: target_verified
  merge_status: pending
  deployment_status: pending
  production_verification_status: pending
candidate:
  commit: "abc123"
  evidence_manifest: "candidate-evidence.json"
  status: target_verified
coordination:
  active_started_at: "2026-07-23T00:00:00Z"
  coordination_wait_started_at: ""
  coordination_wait_seconds: 0
created_at: "2026-07-23T00:00:00Z"
updated_at: "2026-07-23T00:00:00Z"
"""

    def validate(self, state: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "program-state.yaml"
            path.write_text(state, encoding="utf-8")
            return run_script(
                "skills/product-to-delivery/scripts/validate_program_state.py",
                str(path),
            )

    def test_program_completes_only_after_all_child_goals_are_terminal(self) -> None:
        result = self.validate(self.complete_state())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_program_rejects_incomplete_child_goal(self) -> None:
        result = self.validate(self.complete_state("DELIVERY_ACTIVE"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PROGRAM_HAS_UNFINISHED_GOALS", result.stderr)


class CandidateEvidenceTests(unittest.TestCase):
    def validate(self, manifest: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate-evidence.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            return run_script(
                "skills/goal-driven-delivery/scripts/validate_candidate_evidence.py",
                str(path),
            )

    @staticmethod
    def manifest() -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "program_id": "program-1",
            "candidate_commit": "abc123",
            "production_fingerprint": "build-1",
            "exact_target": {"route": "/agent"},
            "status": "target_verified",
            "acceptance_claims": ["AC-001", "AC-002"],
            "execution_scenarios": [
                {
                    "scenario_id": "SC-001",
                    "candidate_commit": "abc123",
                    "proves": ["AC-001", "AC-002"],
                    "provider_mode": "sandbox",
                    "status": "passed",
                }
            ],
            "invalidations": [],
            "full_verification": {
                "candidate_commit": "abc123",
                "passed": True,
                "evidence_path": "evidence/full.txt",
            },
            "final_acceptance": {
                "candidate_commit": "abc123",
                "model": "gpt-5.6-terra",
                "reviewer_thread_id": "reviewer-1",
                "implementation_thread_ids": ["implementation-1"],
                "independence_verified": True,
                "verdict": "TARGET_VERIFIED",
            },
        }

    def test_one_scenario_can_prove_multiple_claims(self) -> None:
        result = self.validate(self.manifest())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_candidate_mismatch_invalidates_evidence(self) -> None:
        manifest = self.manifest()
        manifest["execution_scenarios"][0]["candidate_commit"] = "older"
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CANDIDATE_EVIDENCE_MISMATCH", result.stderr)


class TelemetryTests(unittest.TestCase):
    def test_collects_exact_turn_tokens_by_model_and_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            routing = root / "routing.jsonl"
            routing.write_text(
                json.dumps(
                    routing_record(
                        "turn-1",
                        "implementation",
                        "gpt-5.6-terra",
                        phase="implementation",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            rollout = sessions / "rollout-thread-1.jsonl"
            events = [
                {
                    "timestamp": "2026-07-23T00:00:00Z",
                    "type": "turn_context",
                    "payload": {"turn_id": "turn-1", "model": "gpt-5.6-terra"},
                },
                {
                    "timestamp": "2026-07-23T00:00:02Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 20,
                                "output_tokens": 10,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 110,
                            }
                        },
                    },
                },
                {
                    "timestamp": "2026-07-23T00:00:05Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 150,
                                "cached_input_tokens": 40,
                                "output_tokens": 30,
                                "reasoning_output_tokens": 8,
                                "total_tokens": 180,
                            }
                        },
                    },
                },
            ]
            rollout.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )
            result = run_script(
                "scripts/collect_delivery_telemetry.py",
                str(routing),
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
                "--require-complete",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["by_model"]["gpt-5.6-terra"]["total_tokens"], 180)
        self.assertEqual(report["by_model"]["gpt-5.6-terra"]["cached_input_tokens"], 40)
        self.assertEqual(report["turns"][0]["elapsed_seconds"], 5.0)


if __name__ == "__main__":
    unittest.main()
