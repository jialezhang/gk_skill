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
        "allowed_reason": "routing_canary" if task_class.startswith("routing_") else task_class,
    }
    record.update(extra)
    return record


def terra_fallback_attempts(
    controller_thread_id: str = "thread-1",
    call_prefix: str = "spawn-terra",
) -> list[dict[str, object]]:
    return [
        {
            "attempt": attempt,
            "spawn_controller_thread_id": controller_thread_id,
            "spawn_call_id": f"{call_prefix}-{attempt}",
            "failure_reason": "handshake_not_verified",
        }
        for attempt in range(1, 4)
    ]


def sol_fallback_record(
    turn_id: str,
    task_class: str,
    current_model: str = "gpt-5.7-current",
    **extra: object,
) -> dict[str, object]:
    record = routing_record(
        turn_id,
        task_class,
        current_model,
        request_explicit=False,
        allowed_reason="sol_route_fallback",
        routing_surface="main_agent",
        model_selection_scope="current_context",
        write_allowed=task_class not in {"routing_canary", "routing_transition"},
        fallback_attempted=True,
        fallback_from_model="gpt-5.6-sol",
        fallback_failure_reason="model_not_listed",
        fallback_evidence_source="live_model_capabilities",
        fallback_evidence="current routing surface does not list gpt-5.6-sol",
    )
    record.update(extra)
    return record


def luna_fallback_record(
    turn_id: str,
    task_class: str,
    current_model: str = "gpt-5.7-current",
    **extra: object,
) -> dict[str, object]:
    record = routing_record(
        turn_id,
        task_class,
        current_model,
        request_explicit=False,
        allowed_reason="luna_route_fallback",
        routing_surface="main_agent",
        model_selection_scope="current_context",
        write_allowed=task_class not in {"routing_canary", "routing_transition"},
        fallback_attempted=True,
        fallback_from_model="gpt-5.6-luna",
        fallback_failure_reason="model_not_listed",
        fallback_evidence_source="live_routing_surface",
        fallback_evidence="active routing surface does not expose gpt-5.6-luna",
    )
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
            routing_surface="native_subagent",
            model_selection_scope="context_creation",
            fork_turns="none",
        )
        execution = routing_record(
            "implementation-1",
            "implementation",
            "gpt-5.6-terra",
            handshake_turn_id="handshake-1",
        )
        result = self.validate([handshake, execution], "--require-handshake")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_full_history_fork_cannot_claim_terra_override(self) -> None:
        handshake = routing_record(
            "handshake-1",
            "routing_handshake",
            "gpt-5.6-terra",
            phase="handshake",
            write_allowed=False,
            routing_surface="native_subagent",
            model_selection_scope="context_creation",
            fork_turns="all",
        )
        result = self.validate([handshake], "--require-handshake")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NATIVE_FULL_HISTORY_MODEL_OVERRIDE_FORBIDDEN", result.stderr)

    def test_native_handshake_can_require_permission_inheritance_evidence(self) -> None:
        handshake = routing_record(
            "handshake-1",
            "routing_handshake",
            "gpt-5.6-terra",
            phase="handshake",
            write_allowed=False,
            routing_surface="native_subagent",
            model_selection_scope="context_creation",
            fork_turns="none",
            parent_permission_mode="bypassPermissions",
            observed_permission_mode="bypassPermissions",
            permission_inherited=True,
            permission_source="hook.SubagentStart.permission_mode",
            route_guard_nonce="0123456789abcdef01234567",
        )
        result = self.validate(
            [handshake],
            "--require-handshake",
            "--require-permission-inheritance",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        handshake["observed_permission_mode"] = "default"
        result = self.validate(
            [handshake],
            "--require-handshake",
            "--require-permission-inheritance",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PERMISSION_INHERITANCE_MISMATCH", result.stderr)

    def test_terra_task_name_does_not_override_runtime_model(self) -> None:
        record = routing_record(
            "implementation-1",
            "implementation",
            "gpt-5.6-terra",
            task_name="material_terra_controller",
            agent_type="executor",
            observed_model="gpt-5.4",
        )
        result = self.validate([record])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_ROUTE_MISMATCH", result.stderr)

    def test_runtime_spawn_call_rejects_forged_fork_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            handshake = routing_record(
                "handshake-1",
                "routing_handshake",
                "gpt-5.6-terra",
                phase="handshake",
                write_allowed=False,
                routing_surface="native_subagent",
                model_selection_scope="context_creation",
                fork_turns="none",
                spawn_controller_thread_id="controller-thread",
                spawn_call_id="spawn-call-1",
            )
            routing = root / "routing.jsonl"
            routing.write_text(json.dumps(handshake) + "\n", encoding="utf-8")
            (sessions / "rollout-thread-1.jsonl").write_text(
                json.dumps(
                    {
                        "type": "turn_context",
                        "payload": {
                            "turn_id": "handshake-1",
                            "model": "gpt-5.6-terra",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sessions / "rollout-controller-thread.jsonl").write_text(
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "namespace": "collaboration",
                            "name": "spawn_agent",
                            "call_id": "spawn-call-1",
                            "arguments": json.dumps(
                                {
                                    "task_name": "material_terra_controller",
                                    "agent_type": "executor",
                                    "fork_turns": "all",
                                }
                            ),
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = run_script(
                "scripts/validate_model_routing.py",
                str(routing),
                "--require-runtime-evidence",
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NATIVE_SPAWN_MODEL_MISMATCH", result.stderr)
        self.assertIn("NATIVE_SPAWN_FORK_MISMATCH", result.stderr)

    def test_execution_without_handshake_is_rejected(self) -> None:
        result = self.validate(
            [routing_record("implementation-1", "implementation", "gpt-5.6-terra")],
            "--require-handshake",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_HANDSHAKE_REQUIRED", result.stderr)

    def test_sol_task_continues_on_current_model_when_sol_is_unavailable(self) -> None:
        fallback = sol_fallback_record("plan-fallback-1", "implementation_plan")
        result = self.validate([fallback], "--require-handshake")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_sol_fallback_runtime_evidence_accepts_the_actual_current_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            fallback = sol_fallback_record("plan-fallback-1", "implementation_plan")
            routing = root / "routing.jsonl"
            routing.write_text(json.dumps(fallback) + "\n", encoding="utf-8")
            (sessions / "rollout-thread-1.jsonl").write_text(
                json.dumps(
                    {
                        "type": "turn_context",
                        "payload": {
                            "turn_id": "plan-fallback-1",
                            "model": "gpt-5.7-current",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = run_script(
                "scripts/validate_model_routing.py",
                str(routing),
                "--require-handshake",
                "--require-runtime-evidence",
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_sol_fallback_requires_live_unavailability_evidence(self) -> None:
        fallback = sol_fallback_record("plan-fallback-1", "implementation_plan")
        fallback.pop("fallback_evidence")
        result = self.validate([fallback], "--require-handshake")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOL_FALLBACK_EVIDENCE_REQUIRED", result.stderr)

    def test_luna_task_continues_on_current_model_when_luna_is_unavailable(self) -> None:
        fallback = luna_fallback_record("verification-fallback-1", "routine_verification")
        result = self.validate([fallback], "--require-handshake")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_luna_fallback_requires_live_surface_evidence(self) -> None:
        fallback = luna_fallback_record("verification-fallback-1", "routine_verification")
        fallback.pop("fallback_evidence")
        result = self.validate([fallback], "--require-handshake")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("LUNA_FALLBACK_EVIDENCE_REQUIRED", result.stderr)

    def test_routing_canary_accepts_current_model_for_unavailable_sol(self) -> None:
        records: list[dict[str, object]] = []
        for short, model in (
            ("terra", "gpt-5.6-terra"),
            ("luna", "gpt-5.6-luna"),
        ):
            for phase in ("initial", "followup"):
                records.append(
                    routing_record(
                        f"canary-{short}-{phase}",
                        "routing_canary",
                        model,
                        thread_id=f"canary-{short}",
                        phase=phase,
                    )
                )
        for phase in ("initial", "followup"):
            records.append(
                sol_fallback_record(
                    f"canary-sol-fallback-{phase}",
                    "routing_canary",
                    thread_id="canary-sol-fallback",
                    phase=phase,
                )
            )
        for index, model in enumerate(
            ("gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.7-current", "gpt-5.6-terra"),
            1,
        ):
            if index == 3:
                record = sol_fallback_record(
                    f"transition-{index}",
                    "routing_transition",
                    current_model=model,
                    thread_id="transition-thread",
                    phase="transition",
                    sequence_index=index,
                )
            else:
                record = routing_record(
                    f"transition-{index}",
                    "routing_transition",
                    model,
                    thread_id="transition-thread",
                    phase="transition",
                    sequence_index=index,
                )
            records.append(record)
        result = self.validate(
            records,
            "--require-canary",
            "--require-transition-canary",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_main_agent_continues_with_current_model_when_terra_switch_fails(self) -> None:
        fallback = routing_record(
            "implementation-fallback-1",
            "implementation",
            "gpt-5.6-sol",
            allowed_reason="terra_route_fallback",
            routing_surface="main_agent",
            model_selection_scope="current_context",
            write_allowed=True,
            fallback_attempted=True,
            fallback_from_model="gpt-5.6-terra",
            fallback_attempts=terra_fallback_attempts(),
        )
        result = self.validate([fallback], "--require-handshake")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_main_agent_cannot_claim_fallback_without_a_terra_attempt(self) -> None:
        fallback = routing_record(
            "implementation-fallback-1",
            "implementation",
            "gpt-5.6-sol",
            allowed_reason="terra_route_fallback",
            routing_surface="main_agent",
            model_selection_scope="current_context",
            write_allowed=True,
        )
        result = self.validate([fallback], "--require-handshake")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("TERRA_FALLBACK_EVIDENCE_REQUIRED", result.stderr)

    def test_main_agent_cannot_fallback_after_only_two_terra_attempts(self) -> None:
        fallback = routing_record(
            "implementation-fallback-1",
            "implementation",
            "gpt-5.6-sol",
            allowed_reason="terra_route_fallback",
            routing_surface="main_agent",
            model_selection_scope="current_context",
            write_allowed=True,
            fallback_attempted=True,
            fallback_from_model="gpt-5.6-terra",
            fallback_attempts=terra_fallback_attempts()[:2],
        )
        result = self.validate([fallback], "--require-handshake")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("TERRA_FALLBACK_REQUIRES_THREE_ATTEMPTS", result.stderr)

    def test_fallback_runtime_evidence_proves_the_failed_terra_spawn_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            fallback = routing_record(
                "implementation-fallback-1",
                "implementation",
                "gpt-5.6-sol",
                allowed_reason="terra_route_fallback",
                routing_surface="main_agent",
                model_selection_scope="current_context",
                write_allowed=True,
                fallback_attempted=True,
                fallback_from_model="gpt-5.6-terra",
                fallback_attempts=terra_fallback_attempts(),
            )
            routing = root / "routing.jsonl"
            routing.write_text(json.dumps(fallback) + "\n", encoding="utf-8")
            (sessions / "rollout-thread-1.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "turn_context",
                                "payload": {
                                    "turn_id": "implementation-fallback-1",
                                    "model": "gpt-5.6-sol",
                                },
                            }
                        ),
                        *[
                            json.dumps(
                                {
                                    "type": "response_item",
                                    "payload": {
                                        "type": "function_call",
                                        "namespace": "collaboration",
                                        "name": "spawn_agent",
                                        "call_id": f"spawn-terra-{attempt}",
                                        "arguments": json.dumps(
                                            {
                                                "task_name": "terra_implementation",
                                                "model": "gpt-5.6-terra",
                                                "fork_turns": "none",
                                            }
                                        ),
                                    },
                                }
                            )
                            for attempt in range(1, 4)
                        ],
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = run_script(
                "scripts/validate_model_routing.py",
                str(routing),
                "--require-handshake",
                "--require-runtime-evidence",
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
            )
        self.assertEqual(result.returncode, 0, result.stderr)

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

    def test_current_program_schema_requires_ready_receipt_for_complete(self) -> None:
        state = self.complete_state().replace('schema_version: "1.0"', 'schema_version: "1.2"')
        state = state.replace(
            'created_at: "2026-07-23T00:00:00Z"',
            'completion_receipt:\n  status: pending\n  path: ""\n  sha256: ""\ncreated_at: "2026-07-23T00:00:00Z"',
        )
        result = self.validate(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("COMPLETE_REQUIRES_READY_COMPLETION_RECEIPT", result.stderr)

        state = state.replace("status: pending\n  path: \"\"\n  sha256: \"\"", "status: ready\n  path: \"receipt.json\"\n  sha256: \"abc123\"")
        result = self.validate(state)
        self.assertEqual(result.returncode, 0, result.stderr)


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
            "schema_version": "1.1",
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
                    "evidence_id": "EV-SC-001",
                }
            ],
            "invalidations": [],
            "evidence_records": [
                {
                    "evidence_id": "EV-SC-001",
                    "kind": "scenario",
                    "status": "accepted",
                    "candidate_commit": "abc123",
                    "evidence_path": "evidence/scenario.txt",
                },
                {
                    "evidence_id": "EV-FULL",
                    "kind": "full_verification",
                    "status": "accepted",
                    "candidate_commit": "abc123",
                    "evidence_path": "evidence/full.txt",
                },
                {
                    "evidence_id": "EV-FINAL",
                    "kind": "final_acceptance",
                    "status": "accepted",
                    "candidate_commit": "abc123",
                    "evidence_path": "evidence/final.txt",
                },
            ],
            "runtime_provenance": {
                "status": "verified",
                "candidate_commit": "abc123",
                "target_kind": "service",
                "evidence_path": "evidence/runtime.json",
                "observed_at": "2026-07-23T00:00:00Z",
                "required_observation_ids": ["launch", "process", "build", "target", "cleanup"],
                "observations": [
                    {
                        "observation_id": item,
                        "status": "passed",
                        "source": f"evidence/{item}.txt",
                    }
                    for item in ("launch", "process", "build", "target", "cleanup")
                ],
                "not_applicable_reason": "",
            },
            "full_verification": {
                "candidate_commit": "abc123",
                "passed": True,
                "evidence_path": "evidence/full.txt",
                "evidence_id": "EV-FULL",
            },
            "final_acceptance": {
                "candidate_commit": "abc123",
                "model": "gpt-5.6-terra",
                "reviewer_thread_id": "reviewer-1",
                "reviewer_turn_id": "reviewer-turn-1",
                "implementation_thread_ids": ["implementation-1"],
                "independence_verified": True,
                "verdict": "TARGET_VERIFIED",
                "evidence_id": "EV-FINAL",
            },
        }

    def test_one_scenario_can_prove_multiple_claims(self) -> None:
        result = self.validate(self.manifest())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_candidate_mismatch_invalidates_evidence(self) -> None:
        manifest = self.manifest()
        scenarios = manifest["execution_scenarios"]
        self.assertIsInstance(scenarios, list)
        assert isinstance(scenarios, list)
        scenario = scenarios[0]
        self.assertIsInstance(scenario, dict)
        assert isinstance(scenario, dict)
        scenario["candidate_commit"] = "older"
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CANDIDATE_EVIDENCE_MISMATCH", result.stderr)

    def test_invalidated_evidence_cannot_back_a_passed_scenario(self) -> None:
        manifest = self.manifest()
        manifest["evidence_records"][0].update(
            {
                "status": "invalidated",
                "invalidation_reason": "candidate changed",
                "invalidated_by": "commit:def456",
            }
        )
        manifest["execution_scenarios"][0]["evidence_id"] = "EV-SC-001"
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("referenced evidence is not accepted", result.stderr)

    def test_runtime_provenance_must_match_candidate(self) -> None:
        manifest = self.manifest()
        manifest["runtime_provenance"]["candidate_commit"] = "older"
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RUNTIME_PROVENANCE_CANDIDATE_MISMATCH", result.stderr)

    def test_final_acceptance_accepts_audited_terra_fallback(self) -> None:
        manifest = self.manifest()
        acceptance = manifest["final_acceptance"]
        self.assertIsInstance(acceptance, dict)
        assert isinstance(acceptance, dict)
        acceptance.update(
            model="gpt-5.7-current",
            model_route="terra_route_fallback",
            fallback_from_model="gpt-5.6-terra",
        )
        result = self.validate(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)


class CompletionGateTests(unittest.TestCase):
    @staticmethod
    def terminal_delivery_state(
        program_path: Path, candidate_path: Path, telemetry_path: Path
    ) -> str:
        return f"""\
schema_version: "1.2"
delivery_id: "delivery-1"
status: GOAL_TARGET_VERIFIED
controller:
  role: terra_delivery
  agent_id: "impl-thread"
  lease_updated_at: "2026-07-23T00:00:00Z"
program:
  program_id: "program-1"
  program_state_path: "{program_path}"
  scope_assessment_path: "scope-assessment.yaml"
  split_decision: single_goal
  integration_status: not_required
goal:
  objective: "deliver"
  status: complete
  session_id: "program-thread"
  worktree: "/tmp/worktree"
  branch: "codex/test"
  development_port: null
artifacts:
  prd_path: "spec.md"
  prd_version: "1.0.0"
  plan_path: "plan.md"
  plan_version: "1.0.0"
  tasks_path: "tasks.md"
  tasks_version: "1.0.0"
  verification_path: "verification.md"
  verification_version: "1.0.0"
target_identity: {{}}
model_routing_log: "model-routing.jsonl"
model_canary_status: passed
model_handshake_status: passed
agent_budget:
  normal_target: 8
  soft_limit: 12
  hard_limit: 20
  spawned_total: 2
  max_nesting_depth: 1
  max_parallel_goal_sessions: 3
tasks: {{}}
gates: {{}}
checkpoints: []
attempts: []
active_agents: []
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
candidate:
  commit: "abc123"
  evidence_manifest: "{candidate_path}"
  status: target_verified
stage_user_journeys: []
test_evidence:
  baseline_manifest: "baseline.json"
  impact_map: "impact.json"
  evidence_index: "evidence.json"
completion_telemetry:
  status: captured
  snapshot_path: "{telemetry_path}"
  captured_at: "2026-07-23T00:00:00Z"
  capture_event: before_terminal_transition
  source: runtime_turn_telemetry
  unavailable_fields: []
escalations: []
decisions: []
evidence: []
stale_items: []
next_actions: []
created_at: "2026-07-23T00:00:00Z"
updated_at: "2026-07-23T00:00:00Z"
"""

    @staticmethod
    def complete_routing_records() -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for short, model in (
            ("sol", "gpt-5.6-sol"),
            ("terra", "gpt-5.6-terra"),
            ("luna", "gpt-5.6-luna"),
        ):
            for phase in ("initial", "followup"):
                records.append(
                    routing_record(
                        f"canary-{short}-{phase}",
                        "routing_canary",
                        model,
                        thread_id=f"canary-{short}",
                        phase=phase,
                    )
                )
        for index, model in enumerate(
            (
                "gpt-5.6-terra",
                "gpt-5.6-luna",
                "gpt-5.6-sol",
                "gpt-5.6-terra",
            ),
            1,
        ):
            records.append(
                routing_record(
                    f"transition-{index}",
                    "routing_transition",
                    model,
                    thread_id="transition-thread",
                    phase="transition",
                    sequence_index=index,
                )
            )
        for thread_id, handshake_id, execution_id, task_class in (
            ("impl-thread", "impl-handshake", "implementation-turn", "implementation"),
            ("reviewer-1", "review-handshake", "reviewer-turn-1", "final_target_acceptance"),
        ):
            spawn_call_id = f"spawn-{thread_id}"
            records.append(
                routing_record(
                    handshake_id,
                    "routing_handshake",
                    "gpt-5.6-terra",
                    thread_id=thread_id,
                    phase="handshake",
                    write_allowed=False,
                    routing_surface="native_subagent",
                    model_selection_scope="context_creation",
                    fork_turns="none",
                    spawn_controller_thread_id="controller-thread",
                    spawn_call_id=spawn_call_id,
                    parent_permission_mode="bypassPermissions",
                    observed_permission_mode="bypassPermissions",
                    permission_inherited=True,
                    permission_source="hook.SubagentStart.permission_mode",
                    route_guard_nonce=(
                        "0123456789abcdef01234567"
                        if thread_id == "impl-thread"
                        else "89abcdef0123456789abcdef"
                    ),
                )
            )
            extra: dict[str, object] = {"handshake_turn_id": handshake_id}
            if task_class == "final_target_acceptance":
                extra.update(
                    implementation_thread_ids=["impl-thread"],
                    independence_verified=True,
                )
            records.append(
                routing_record(
                    execution_id,
                    task_class,
                    "gpt-5.6-terra",
                    thread_id=thread_id,
                    **extra,
                )
            )
        return records

    def run_complete_gate(
        self,
        records: list[dict[str, object]],
        issue_receipt: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            routing = root / "model-routing.jsonl"
            routing.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            by_thread: dict[str, list[dict[str, object]]] = {}
            for record in records:
                by_thread.setdefault(str(record["thread_id"]), []).append(record)
            for thread_id, thread_records in by_thread.items():
                rollout = sessions / f"rollout-{thread_id}.jsonl"
                rollout.write_text(
                    "".join(
                        json.dumps(
                            {
                                "type": "turn_context",
                                "payload": {
                                    "turn_id": record["turn_id"],
                                    "model": record["observed_model"],
                                },
                            }
                        )
                        + "\n"
                        for record in thread_records
                    ),
                    encoding="utf-8",
                )
            spawn_specs = [
                ("impl-thread", "spawn-impl-thread"),
                ("impl-thread", "spawn-impl-thread-1"),
                ("impl-thread", "spawn-impl-thread-2"),
                ("impl-thread", "spawn-impl-thread-3"),
                ("reviewer-1", "spawn-reviewer-1"),
                ("reviewer-1", "spawn-reviewer-1-1"),
                ("reviewer-1", "spawn-reviewer-1-2"),
                ("reviewer-1", "spawn-reviewer-1-3"),
            ]
            spawn_events = [
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "namespace": "collaboration",
                        "name": "spawn_agent",
                        "call_id": call_id,
                        "arguments": json.dumps(
                            {
                                "task_name": thread_id,
                                "fork_turns": "none",
                                "model": "gpt-5.6-terra",
                            }
                        ),
                    },
                }
                for thread_id, call_id in spawn_specs
            ]
            (sessions / "rollout-controller-thread.jsonl").write_text(
                "".join(json.dumps(event) + "\n" for event in spawn_events),
                encoding="utf-8",
            )
            candidate_manifest = CandidateEvidenceTests.manifest()
            final_acceptance = candidate_manifest["final_acceptance"]
            self.assertIsInstance(final_acceptance, dict)
            assert isinstance(final_acceptance, dict)
            final_acceptance["implementation_thread_ids"] = [
                "impl-thread"
            ]
            final_route = next(
                (
                    record
                    for record in records
                    if record.get("task_class") == "final_target_acceptance"
                    and record.get("thread_id") == "reviewer-1"
                    and record.get("turn_id") == "reviewer-turn-1"
                ),
                None,
            )
            if final_route is not None:
                final_acceptance["model"] = final_route["observed_model"]
                if final_route.get("allowed_reason") == "terra_route_fallback":
                    final_acceptance["model_route"] = "terra_route_fallback"
                    final_acceptance["fallback_from_model"] = "gpt-5.6-terra"
            candidate = root / "candidate-evidence.json"
            candidate.write_text(json.dumps(candidate_manifest), encoding="utf-8")
            telemetry = root / "completion-telemetry.json"
            telemetry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.1",
                        "by_model": {},
                        "by_phase": {},
                        "completion_snapshot": {
                            "status": "captured",
                            "capture_event": "before_terminal_transition",
                            "captured_at": "2026-07-23T00:00:00Z",
                            "source": "runtime_turn_telemetry",
                            "unavailable_fields": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            program = root / "program-state.yaml"
            program.write_text(ProgramLifecycleTests.complete_state(), encoding="utf-8")
            delivery = root / "delivery-state.yaml"
            delivery.write_text(
                self.terminal_delivery_state(program, candidate, telemetry),
                encoding="utf-8",
            )
            command = [
                "scripts/validate_completion_gate.py",
                "--routing-log",
                str(routing),
                "--delivery-state",
                str(delivery),
                "--candidate-evidence",
                str(candidate),
                "--program-state",
                str(program),
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
            ]
            receipt = root / "completion-receipt.json"
            if issue_receipt:
                command.extend(["--receipt", str(receipt)])
            result = run_script(*command)
            if issue_receipt and result.returncode == 0:
                receipt_result = run_script(
                    "scripts/validate_completion_receipt.py", str(receipt)
                )
                self.assertEqual(receipt_result.returncode, 0, receipt_result.stderr)
                receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
                self.assertEqual(receipt_data["status"], "ready")
                self.assertEqual(receipt_data["candidate_commit"], "abc123")
                self.assertTrue(
                    any(
                        key.startswith("runtime_rollout_")
                        for key in receipt_data["inputs"]
                    ),
                    "completion receipt must bind the raw rollout evidence",
                )
            return result

    def test_complete_raw_evidence_gate_passes(self) -> None:
        result = self.run_complete_gate(self.complete_routing_records())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_current_delivery_schema_allows_pending_receipt_before_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.terminal_delivery_state(
                root / "program.yaml", root / "candidate.json", root / "telemetry.json"
            )
            state = state.replace('schema_version: "1.2"', 'schema_version: "1.3"')
            state = state.replace(
                "status: GOAL_TARGET_VERIFIED",
                'status: GOAL_TARGET_VERIFIED\nproject_profile_path: "project-profile.json"',
            )
            state = state.replace(
                "escalations: []",
                'completion_receipt:\n  status: pending\n  path: ""\n  sha256: ""\nescalations: []',
            )
            path = root / "delivery-state.yaml"
            path.write_text(state, encoding="utf-8")
            result = run_script(
                "skills/goal-driven-delivery/scripts/validate_delivery_state.py",
                str(path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            path.write_text(
                state.replace("status: GOAL_TARGET_VERIFIED", "status: COMPLETE"),
                encoding="utf-8",
            )
            result = run_script(
                "skills/goal-driven-delivery/scripts/validate_delivery_state.py",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("COMPLETE_REQUIRES_READY_COMPLETION_RECEIPT", result.stderr)

    def test_complete_gate_issues_revalidatable_receipt(self) -> None:
        result = self.run_complete_gate(
            self.complete_routing_records(), issue_receipt=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_complete_gate_uses_raw_native_evidence_without_route_guard_nonce(self) -> None:
        records = self.complete_routing_records()
        optional_hook_fields = {
            "parent_permission_mode",
            "observed_permission_mode",
            "permission_inherited",
            "permission_source",
            "route_guard_nonce",
        }
        for record in records:
            for field in optional_hook_fields:
                record.pop(field, None)
        result = self.run_complete_gate(records)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_complete_gate_does_not_block_when_sol_is_unavailable(self) -> None:
        records: list[dict[str, object]] = []
        for record in self.complete_routing_records():
            if record.get("thread_id") == "canary-sol":
                records.append(
                    sol_fallback_record(
                        str(record["turn_id"]),
                        "routing_canary",
                        thread_id="canary-sol",
                        phase=str(record["phase"]),
                    )
                )
            elif record.get("turn_id") == "transition-3":
                records.append(
                    sol_fallback_record(
                        "transition-3",
                        "routing_transition",
                        thread_id="transition-thread",
                        phase="transition",
                        sequence_index=3,
                    )
                )
            else:
                records.append(record)
        result = self.run_complete_gate(records)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_complete_gate_does_not_block_when_luna_is_unavailable(self) -> None:
        records: list[dict[str, object]] = []
        for record in self.complete_routing_records():
            if record.get("thread_id") == "canary-luna":
                records.append(
                    luna_fallback_record(
                        str(record["turn_id"]),
                        "routing_canary",
                        thread_id="canary-luna",
                        phase=str(record["phase"]),
                    )
                )
            elif record.get("turn_id") == "transition-2":
                records.append(
                    luna_fallback_record(
                        "transition-2",
                        "routing_transition",
                        thread_id="transition-thread",
                        phase="transition",
                        sequence_index=2,
                    )
                )
            else:
                records.append(record)
        result = self.run_complete_gate(records)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_complete_gate_accepts_audited_main_agent_fallback(self) -> None:
        records = [
            record
            for record in self.complete_routing_records()
            if record.get("turn_id") not in {"impl-handshake", "implementation-turn"}
        ]
        records.append(
            routing_record(
                "implementation-fallback-1",
                "implementation",
                "gpt-5.6-sol",
                thread_id="impl-thread",
                allowed_reason="terra_route_fallback",
                routing_surface="main_agent",
                model_selection_scope="current_context",
                write_allowed=True,
                fallback_attempted=True,
                fallback_from_model="gpt-5.6-terra",
                fallback_attempts=terra_fallback_attempts(
                    "controller-thread",
                    "spawn-impl-thread",
                ),
            )
        )
        result = self.run_complete_gate(records)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_complete_gate_accepts_independent_terra_final_acceptance_fallback(self) -> None:
        records = [
            record
            for record in self.complete_routing_records()
            if record.get("turn_id") not in {"review-handshake", "reviewer-turn-1"}
        ]
        records.append(
            routing_record(
                "reviewer-turn-1",
                "final_target_acceptance",
                "gpt-5.7-current",
                thread_id="reviewer-1",
                request_explicit=False,
                allowed_reason="terra_route_fallback",
                routing_surface="native_subagent",
                model_selection_scope="context_creation",
                write_allowed=False,
                fallback_attempted=True,
                fallback_from_model="gpt-5.6-terra",
                fallback_attempts=terra_fallback_attempts(
                    "controller-thread",
                    "spawn-reviewer-1",
                ),
                implementation_thread_ids=["impl-thread"],
                independence_verified=True,
            )
        )
        result = self.run_complete_gate(records)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_declared_pass_cannot_replace_raw_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing = root / "model-routing.jsonl"
            routing.write_text(
                json.dumps(
                    routing_record(
                        "implementation-1",
                        "implementation",
                        "gpt-5.6-terra",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            delivery = root / "delivery-state.yaml"
            delivery.write_text(
                (
                    PLUGIN_ROOT
                    / "skills/goal-driven-delivery/assets/delivery-state-template.yaml"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            candidate = root / "candidate-evidence.json"
            candidate.write_text(
                json.dumps(CandidateEvidenceTests.manifest()),
                encoding="utf-8",
            )
            program = root / "program-state.yaml"
            program.write_text(
                ProgramLifecycleTests.complete_state(),
                encoding="utf-8",
            )
            result = run_script(
                "scripts/validate_completion_gate.py",
                "--routing-log",
                str(routing),
                "--delivery-state",
                str(delivery),
                "--candidate-evidence",
                str(candidate),
                "--program-state",
                str(program),
                "--sessions-root",
                str(root / "sessions"),
                "--archived-root",
                str(root / "archived"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RUNTIME_TURN_NOT_FOUND", result.stderr)


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

    def test_completion_snapshot_marks_missing_turns_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing = root / "routing.jsonl"
            routing.write_text(
                json.dumps(
                    routing_record("turn-missing", "implementation", "gpt-5.6-terra")
                )
                + "\n",
                encoding="utf-8",
            )
            output = root / "completion-telemetry.json"
            result = run_script(
                "scripts/collect_delivery_telemetry.py",
                str(routing),
                "--sessions-root",
                str(root / "sessions"),
                "--archived-root",
                str(root / "archived"),
                "--completion-snapshot",
                "--output",
                str(output),
            )
            validation = run_script("scripts/validate_completion_telemetry.py", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(validation.returncode, 0, validation.stderr)


if __name__ == "__main__":
    unittest.main()
