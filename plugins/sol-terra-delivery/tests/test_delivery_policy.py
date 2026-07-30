#!/usr/bin/env python3
"""Behavioral contracts for the Sol Terra Delivery routing policy."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills"


def run_script(relative: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / relative), *args],
        text=True,
        capture_output=True,
        check=False,
    )


class ScopeAssessmentPolicyTests(unittest.TestCase):
    def test_scope_assessment_skill_and_validator_exist(self) -> None:
        self.assertTrue((SKILL_ROOT / "assess-goal-scope" / "SKILL.md").is_file())
        self.assertTrue(
            (SKILL_ROOT / "assess-goal-scope" / "scripts" / "validate_scope_assessment.py").is_file()
        )

    def test_p80_over_eight_hours_requires_split_recommendation(self) -> None:
        assessment = """\
schema_version: "1.0"
assessment_id: "scope-001"
p50_hours: 6
p80_hours: 9
p90_hours: 12
expected_files: 24
domains: [frontend, api, authorization, e2e]
uncertainty: high
parallelizable: true
suggested_goals: 2
critical_path_p80_hours: 7
split_recommended: false
split_strength: recommended
split_decision: awaiting_user
decision_source: pending
decision_timeout_seconds: 240
work_packages: []
dependency_graph: []
conflict_graph: []
created_at: "2026-07-21T00:00:00Z"
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope-assessment.yaml"
            path.write_text(assessment, encoding="utf-8")
            result = run_script(
                "skills/assess-goal-scope/scripts/validate_scope_assessment.py",
                str(path),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("p80_hours > 8", result.stderr)

    def test_timeout_resolution_is_single_goal(self) -> None:
        assessment = """\
schema_version: "1.0"
assessment_id: "scope-002"
p50_hours: 7
p80_hours: 11
p90_hours: 15
expected_files: 42
domains: [frontend, api, runtime, data, e2e]
uncertainty: high
parallelizable: true
suggested_goals: 3
critical_path_p80_hours: 8
split_recommended: true
split_strength: strong
split_decision: single_goal
decision_source: timeout_default_single
decision_timeout_seconds: 240
work_packages: []
dependency_graph: []
conflict_graph: []
created_at: "2026-07-21T00:00:00Z"
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope-assessment.yaml"
            path.write_text(assessment, encoding="utf-8")
            result = run_script(
                "skills/assess-goal-scope/scripts/validate_scope_assessment.py",
                str(path),
            )
        self.assertEqual(result.returncode, 0, result.stderr)


class ModelRoutingPolicyTests(unittest.TestCase):
    def _validate(
        self,
        records: list[dict[str, object]],
        *extra: str,
        runtime_models: dict[tuple[str, str], str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "model-routing.jsonl"
            path.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            sessions = root / "sessions"
            sessions.mkdir()
            for (thread_id, turn_id), model in (runtime_models or {}).items():
                rollout = sessions / f"rollout-test-{thread_id}.jsonl"
                with rollout.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps({
                        "timestamp": "2026-07-21T00:00:00Z",
                        "type": "turn_context",
                        "payload": {"turn_id": turn_id, "model": model},
                    }) + "\n")
            return run_script(
                "scripts/validate_model_routing.py",
                str(path),
                "--sessions-root",
                str(sessions),
                *extra,
            )

    @staticmethod
    def _record(
        turn_id: str,
        task_class: str,
        model: str,
        *,
        thread_id: str = "thread-1",
        phase: str = "execution",
        sequence_index: int | None = None,
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "thread_id": thread_id,
            "turn_id": turn_id,
            "task_class": task_class,
            "requested_model": model,
            "request_explicit": True,
            "observed_model": model,
            "observed_source": "rollout.turn_context.payload.model",
            "phase": phase,
            "verified": True,
            "allowed_reason": "routing_canary" if task_class.startswith("routing_") else task_class,
        }
        if sequence_index is not None:
            record["sequence_index"] = sequence_index
        return record

    def test_each_turn_must_observe_the_requested_model(self) -> None:
        record = self._record("implementation-1", "implementation", "gpt-5.6-terra")
        record["observed_model"] = "gpt-5.6-sol"
        result = self._validate([record])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_ROUTE_MISMATCH", result.stderr)

    def test_canary_requires_initial_and_followup_for_each_model(self) -> None:
        records: list[dict[str, object]] = []
        runtime: dict[tuple[str, str], str] = {}
        for short, model in (
            ("sol", "gpt-5.6-sol"),
            ("terra", "gpt-5.6-terra"),
            ("luna", "gpt-5.6-luna"),
        ):
            for phase in ("initial", "followup"):
                thread_id = f"thread-{short}"
                turn_id = f"canary-{short}-{phase}"
                records.append(self._record(
                    turn_id,
                    "routing_canary",
                    model,
                    thread_id=thread_id,
                    phase=phase,
                ))
                runtime[(thread_id, turn_id)] = model
        result = self._validate(
            records,
            "--require-canary",
            "--require-runtime-evidence",
            runtime_models=runtime,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_incomplete_followup_canary_is_rejected(self) -> None:
        records = [
            self._record(
                f"canary-{short}-initial",
                "routing_canary",
                model,
                thread_id=f"thread-{short}",
                phase="initial",
            )
            for short, model in (
                ("sol", "gpt-5.6-sol"),
                ("terra", "gpt-5.6-terra"),
                ("luna", "gpt-5.6-luna"),
            )
        ]
        result = self._validate(records, "--require-canary")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_CANARY_INCOMPLETE", result.stderr)

    def test_runtime_rollout_rejects_forged_observed_model(self) -> None:
        record = self._record("implementation-1", "implementation", "gpt-5.6-terra")
        result = self._validate(
            [record],
            "--require-runtime-evidence",
            runtime_models={("thread-1", "implementation-1"): "gpt-5.6-sol"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RUNTIME_MODEL_MISMATCH", result.stderr)

    def test_followup_without_explicit_model_is_rejected(self) -> None:
        record = self._record(
            "terra-followup",
            "routing_canary",
            "gpt-5.6-terra",
            phase="followup",
        )
        record["request_explicit"] = False
        result = self._validate([record])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_REQUEST_NOT_EXPLICIT", result.stderr)

    def test_same_thread_transition_sequence_is_verified(self) -> None:
        models = [
            "gpt-5.6-terra",
            "gpt-5.6-luna",
            "gpt-5.6-sol",
            "gpt-5.6-terra",
        ]
        records = [
            self._record(
                f"transition-{index}",
                "routing_transition",
                model,
                thread_id="thread-transition",
                phase="transition",
                sequence_index=index,
            )
            for index, model in enumerate(models, 1)
        ]
        runtime = {
            ("thread-transition", f"transition-{index}"): model
            for index, model in enumerate(models, 1)
        }
        result = self._validate(
            records,
            "--require-transition-canary",
            "--require-runtime-evidence",
            runtime_models=runtime,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_task_class_is_rejected(self) -> None:
        result = self._validate([
            self._record("unknown-1", "mystery_work", "gpt-5.6-terra")
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("UNKNOWN_TASK_CLASS", result.stderr)

    def test_sol_is_rejected_for_routine_verification(self) -> None:
        result = self._validate([
            self._record("verify-1", "routine_verification", "gpt-5.6-sol")
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOL_REASON_NOT_ALLOWED", result.stderr)


class DeliveryGovernanceTextTests(unittest.TestCase):
    def test_technical_change_routes_through_explicit_prd_decision(self) -> None:
        controller = (SKILL_ROOT / "product-to-delivery" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        routing = (
            SKILL_ROOT / "product-to-delivery" / "references" / "stage-routing.md"
        ).read_text(encoding="utf-8")
        lifecycle = (
            SKILL_ROOT / "product-to-delivery" / "references" / "lifecycle-contract.md"
        ).read_text(encoding="utf-8")

        for text in (controller, routing, lifecycle):
            self.assertIn("PRD_NOT_REQUIRED", text)
            self.assertIn("technical-change lane", text)
        self.assertIn("ask whether a PRD is needed", controller)
        self.assertIn("Silence does not choose", controller)
        self.assertNotIn(
            "Discovery complete, no PRD | current main agent runs `create-product-prd`",
            routing,
        )

    def test_prd_skip_does_not_enter_prd_dependent_delivery_skills(self) -> None:
        routing = (
            SKILL_ROOT / "product-to-delivery" / "references" / "stage-routing.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Do not invoke `assess-goal-scope`", routing)
        self.assertIn("Do not invoke `create-implementation-plan`", routing)
        self.assertIn("Do not invoke `goal-driven-delivery`", routing)
        self.assertIn("reclassify the task before continuing", routing)

    def test_controller_requires_scope_decision_before_plan(self) -> None:
        text = (SKILL_ROOT / "product-to-delivery" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("$assess-goal-scope", text)
        self.assertIn("240", text)
        self.assertIn("timeout_default_single", text)

    def test_delivery_has_agent_budget_and_checkpoint_contract(self) -> None:
        text = (SKILL_ROOT / "goal-driven-delivery" / "SKILL.md").read_text(encoding="utf-8")
        for required in ("hard limit of 20", "model-routing.jsonl", "commit", "push", "progress report"):
            self.assertIn(required, text)

    def test_final_acceptance_routes_to_independent_terra(self) -> None:
        text = (SKILL_ROOT / "review-delivery-gate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("gpt-5.6-terra", text)
        self.assertIn("independent Terra", text)
        self.assertIn("gpt-5.6-luna", text)

    def test_plan_consumes_scope_and_defines_goal_isolation(self) -> None:
        text = (SKILL_ROOT / "create-implementation-plan" / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "scope-assessment.yaml",
            "program baseline",
            "worktree",
            "checkpoint",
            "current main agent",
            "Do not spawn, create, or delegate",
        ):
            self.assertIn(required, text)

    def test_prd_is_authored_and_reviewed_only_by_main_agent(self) -> None:
        text = (SKILL_ROOT / "create-product-prd" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("gpt-5.6-sol", text)
        self.assertIn("current main agent", text)
        self.assertIn("Do not spawn, create, or delegate", text)
        self.assertNotIn("fresh `gpt-5.6-luna` context", text)
        self.assertNotIn("second Sol reviewer", text)

    def test_controller_keeps_prd_and_plan_work_in_main_agent(self) -> None:
        controller = (SKILL_ROOT / "product-to-delivery" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        revision = (
            SKILL_ROOT / "review-delivery-gate" / "references" / "plan-revision.md"
        ).read_text(encoding="utf-8")
        for text in (controller, revision):
            self.assertIn("current main agent", text)
            self.assertIn("Do not spawn, create, or delegate", text)
        self.assertNotIn("with a Sol-class product agent", controller)
        self.assertNotIn("with a Sol-class planner", controller)

    def test_multi_goal_integration_skill_exists(self) -> None:
        text = (SKILL_ROOT / "integrate-goals" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("integration worktree", text)
        self.assertIn("clean commit", text)


class DeliveryStatePolicyTests(unittest.TestCase):
    def _validate(self, state: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "delivery-state.yaml"
            path.write_text(state, encoding="utf-8")
            return run_script(
                "skills/goal-driven-delivery/scripts/validate_delivery_state.py",
                str(path),
                "--allow-empty",
            )

    def test_twenty_first_agent_is_rejected(self) -> None:
        state = (
            SKILL_ROOT / "goal-driven-delivery" / "assets" / "delivery-state-template.yaml"
        ).read_text(encoding="utf-8").replace("spawned_total: 0", "spawned_total: 21")
        result = self._validate(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AGENT_BUDGET_EXHAUSTED", result.stderr)

    def test_completed_checkpoint_requires_commit_push_and_report(self) -> None:
        state = (
            SKILL_ROOT / "goal-driven-delivery" / "assets" / "delivery-state-template.yaml"
        ).read_text(encoding="utf-8").replace(
            "checkpoints: []",
            """checkpoints:
  - checkpoint_id: CP-01
    status: completed
    commit_sha: ""
    pushed: false
    reported_at: ""
""".rstrip(),
        )
        result = self._validate(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("completed checkpoint CP-01", result.stderr)

    def test_terminal_state_requires_completion_telemetry(self) -> None:
        state = (
            SKILL_ROOT / "goal-driven-delivery" / "assets" / "delivery-state-template.yaml"
        ).read_text(encoding="utf-8")
        state = state.replace("status: DELIVERY_ACTIVE", "status: TARGET_VERIFIED", 1)
        state = state.replace("candidate:\n  commit: \"\"", "candidate:\n  commit: \"abc123\"")
        state = state.replace("evidence_manifest: \"\"", "evidence_manifest: \"candidate.json\"")
        state = state.replace("status: pending\nstage_user_journeys", "status: target_verified\nstage_user_journeys", 1)
        state = state.replace("model_canary_status: pending", "model_canary_status: passed")
        state = state.replace("model_handshake_status: pending", "model_handshake_status: passed")
        state = state.replace("program_state_path: \"\"", "program_state_path: \"program.yaml\"")
        state = state.replace("baseline_manifest: \"\"", "baseline_manifest: \"baseline.json\"")
        state = state.replace("impact_map: \"\"", "impact_map: \"impact.json\"")
        state = state.replace("evidence_index: \"\"", "evidence_index: \"index.json\"")
        for lane in ("implementation", "automation", "exact_target", "release"):
            state = state.replace(f"{lane}_total: 0", f"{lane}_total: 1")
            state = state.replace(f"{lane}_completed: 0", f"{lane}_completed: 1")
        result = self._validate(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("completion_telemetry.status", result.stderr)


class IntegrationPolicyTests(unittest.TestCase):
    def _validate(self, manifest: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "program-integration.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            return run_script(
                "skills/integrate-goals/scripts/validate_integration_manifest.py",
                str(path),
            )

    def test_integration_requires_every_goal_pushed_and_verified(self) -> None:
        result = self._validate(
            {
                "schema_version": "1.0",
                "program_id": "program-1",
                "base_commit": "base123",
                "program_state_valid": False,
                "goals": [
                    {
                        "goal_id": "goal-1",
                        "commit_sha": "abc123",
                        "pushed": False,
                        "target_verified": True,
                        "model_routing_valid": True,
                    }
                ],
                "integration_commit": "",
                "clean_worktree": False,
                "full_verification_passed": False,
                "candidate_evidence_valid": False,
                "final_acceptance_model": "gpt-5.6-terra",
                "final_acceptance_thread_id": "",
                "final_acceptance_turn_id": "",
                "model_routing_log": "",
                "implementation_thread_ids": ["implementation-1"],
                "final_acceptance_independent": False,
                "final_acceptance": "pending",
            }
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("goal-1", result.stderr)

    def test_complete_integration_manifest_passes(self) -> None:
        result = self._validate(
            {
                "schema_version": "1.0",
                "program_id": "program-1",
                "base_commit": "base123",
                "program_state_valid": True,
                "goals": [
                    {
                        "goal_id": "goal-1",
                        "commit_sha": "abc123",
                        "pushed": True,
                        "target_verified": True,
                        "model_routing_valid": True,
                        "evidence_lifecycle_valid": True,
                        "completion_telemetry_snapshot": "telemetry/goal-1.json",
                    }
                ],
                "integration_commit": "def456",
                "clean_worktree": True,
                "full_verification_passed": True,
                "candidate_evidence_valid": True,
                "evidence_lifecycle_valid": True,
                "runtime_provenance": {
                    "status": "verified",
                    "candidate_commit": "def456",
                    "evidence_path": "evidence/runtime.json",
                },
                "goal_telemetry_snapshots": [
                    {"goal_id": "goal-1", "snapshot_path": "telemetry/goal-1.json"}
                ],
                "completion_telemetry": {
                    "status": "captured",
                    "snapshot_path": "telemetry/program.json",
                    "captured_at": "2026-07-23T00:00:00Z",
                    "source": "runtime_turn_telemetry",
                    "unavailable_fields": [],
                },
                "final_acceptance_model": "gpt-5.6-terra",
                "final_acceptance_thread_id": "acceptance-1",
                "final_acceptance_turn_id": "acceptance-turn-1",
                "model_routing_log": "model-routing.jsonl",
                "implementation_thread_ids": ["implementation-1"],
                "final_acceptance_independent": True,
                "final_acceptance": "TARGET_VERIFIED",
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
