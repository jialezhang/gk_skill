#!/usr/bin/env python3
"""Golden-path tests for the project-agnostic delivery contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from delivery_contract import file_digest  # noqa: E402


def run_script(relative: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / relative), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def evidence_manifest() -> dict[str, object]:
    candidate = "candidate-123"
    profile_sha256 = hashlib.sha256(
        json.dumps(project_profile()).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "1.2",
        "program_id": "program-1",
        "candidate_commit": candidate,
        "production_fingerprint": "runtime-1",
        "exact_target": {"component_ids": ["primary-runtime"]},
        "status": "target_verified",
        "candidate_freeze": {
            "status": "frozen",
            "candidate_commit": candidate,
            "frozen_at": "2026-08-05T00:00:00Z",
            "project_profile_path": "project-profile.json",
            "project_profile_sha256": profile_sha256,
            "unresolved_effect_ids": [],
        },
        "acceptance_claims": ["AC-001"],
        "execution_scenarios": [
            {
                "scenario_id": "SC-001",
                "candidate_commit": candidate,
                "proves": ["AC-001"],
                "external_effects": [
                    {
                        "effect_id": "partner-ledger-write",
                        "policy": "sandboxed",
                        "evidence_path": "evidence/effect.json",
                    }
                ],
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
                "candidate_commit": "candidate-122",
                "evidence_path": "evidence/scenario.txt",
                "revalidation": {
                    "candidate_commit": candidate,
                    "result": "accepted",
                    "validated_at": "2026-08-05T00:00:00Z",
                    "invalidation_keys_checked": ["contract", "runtime"],
                    "evidence_path": "evidence/revalidation.txt",
                },
            },
            {
                "evidence_id": "EV-FULL",
                "kind": "full_verification",
                "status": "accepted",
                "candidate_commit": candidate,
                "evidence_path": "evidence/full.txt",
            },
            {
                "evidence_id": "EV-FINAL",
                "kind": "final_acceptance",
                "status": "accepted",
                "candidate_commit": candidate,
                "evidence_path": "evidence/final.txt",
            },
        ],
        "runtime_provenance": {
            "status": "verified",
            "candidate_commit": candidate,
            "target_kind": "service",
            "evidence_path": "evidence/runtime.json",
            "observed_at": "2026-08-05T00:00:00Z",
            "required_observation_ids": ["identity"],
            "observations": [
                {
                    "observation_id": "identity",
                    "status": "passed",
                    "source": "evidence/identity.txt",
                }
            ],
            "not_applicable_reason": "",
        },
        "full_verification": {
            "candidate_commit": candidate,
            "passed": True,
            "evidence_path": "evidence/full.txt",
            "evidence_id": "EV-FULL",
        },
        "final_acceptance": {
            "candidate_commit": candidate,
            "model": "gpt-5.6-terra",
            "reviewer_thread_id": "reviewer-1",
            "reviewer_turn_id": "reviewer-turn-1",
            "implementation_thread_ids": ["implementation-1"],
            "independence_verified": True,
            "verdict": "TARGET_VERIFIED",
            "evidence_id": "EV-FINAL",
        },
    }


def project_profile() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "profile_id": "generic-test",
        "target_components": [
            {
                "component_id": "primary-runtime",
                "kind": "service",
                "identity_requirements": ["revision"],
                "runtime_probes": ["behavior"],
            }
        ],
        "protected_resources": [],
        "external_effects": [
            {
                "effect_id": "partner-ledger-write",
                "policy": "sandboxed",
                "authorization_ref": "",
                "budget_limit": None,
                "verification_mode": "recorded-response",
            }
        ],
        "acceptance_journeys": [
            {
                "journey_id": "operator-completes-cycle",
                "claim_ids": ["AC-001"],
                "target_component_ids": ["primary-runtime"],
            }
        ],
        "verification_commands": [
            {"command_id": "focused", "command": "make test", "tier": "change"}
        ],
        "rollback_actions": [],
    }


class ProjectProfileTests(unittest.TestCase):
    def test_plugin_manifest_exposes_complete_brand_assets(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        interface = manifest["interface"]
        self.assertEqual(interface["brandColor"], "#315EFB")
        for field in ("composerIcon", "logo", "logoDark"):
            asset_path = interface[field]
            self.assertTrue(asset_path.startswith("./assets/"))
            self.assertTrue((PLUGIN_ROOT / asset_path).is_file(), field)

    def validate(self, profile: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project-profile.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            return run_script("scripts/validate_project_profile.py", str(path))

    def test_arbitrary_components_resources_and_effects_are_supported(self) -> None:
        profile = {
            "schema_version": "1.0",
            "profile_id": "warehouse-automation",
            "target_components": [
                {
                    "component_id": "primary-runtime",
                    "kind": "service",
                    "identity_requirements": ["revision", "executor"],
                    "runtime_probes": ["health", "behavior"],
                }
            ],
            "protected_resources": [
                {
                    "resource_id": "customer-ledger",
                    "locator": "state/ledger.db",
                    "write_gate": "explicit-authorization",
                    "backup_action": "backup-ledger",
                    "rollback_action": "restore-ledger",
                }
            ],
            "external_effects": [
                {
                    "effect_id": "partner-ledger-write",
                    "policy": "sandboxed",
                    "authorization_ref": "test-policy",
                    "budget_limit": None,
                    "verification_mode": "recorded-response",
                }
            ],
            "acceptance_journeys": [
                {
                    "journey_id": "operator-completes-cycle",
                    "claim_ids": ["AC-001"],
                    "target_component_ids": ["primary-runtime"],
                }
            ],
            "verification_commands": [
                {"command_id": "focused", "command": "make test", "tier": "change"}
            ],
            "rollback_actions": [
                {
                    "action_id": "restore-ledger",
                    "command": "tools/restore-ledger",
                    "applies_to": ["customer-ledger"],
                }
            ],
        }
        result = self.validate(profile)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_protected_resource_requires_write_and_rollback_gates(self) -> None:
        profile = {
            "schema_version": "1.0",
            "profile_id": "unsafe",
            "target_components": [],
            "protected_resources": [
                {"resource_id": "records", "locator": "records.db"}
            ],
            "external_effects": [],
            "acceptance_journeys": [],
            "verification_commands": [],
            "rollback_actions": [],
        }
        result = self.validate(profile)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PROTECTED_RESOURCE_GATE_INCOMPLETE", result.stderr)

    def test_planning_templates_use_generic_external_effect_language(self) -> None:
        task_template = (
            PLUGIN_ROOT / "skills/create-implementation-plan/assets/tasks-template.md"
        ).read_text(encoding="utf-8")
        verification_template = (
            PLUGIN_ROOT
            / "skills/create-implementation-plan/assets/verification-template.md"
        ).read_text(encoding="utf-8")
        for template in (task_template, verification_template):
            self.assertIn("External effect policy", template)
            self.assertNotIn("Provider mode", template)


class GenericEvidenceTests(unittest.TestCase):
    def validate(self, manifest: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate-evidence.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            profile = path.parent / "project-profile.json"
            profile.write_text(json.dumps(project_profile()), encoding="utf-8")
            return run_script(
                "skills/goal-driven-delivery/scripts/validate_candidate_evidence.py",
                str(path),
                "--project-profile",
                str(profile),
            )

    def test_named_external_effect_and_explicit_revalidation_pass(self) -> None:
        result = self.validate(evidence_manifest())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cross_candidate_evidence_without_revalidation_fails(self) -> None:
        manifest = evidence_manifest()
        del manifest["evidence_records"][0]["revalidation"]
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EVIDENCE_REVALIDATION_REQUIRED", result.stderr)

    def test_terminal_candidate_requires_a_freeze(self) -> None:
        manifest = evidence_manifest()
        del manifest["candidate_freeze"]
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CANDIDATE_FREEZE_REQUIRED", result.stderr)

    def test_scenario_effect_must_match_the_project_profile(self) -> None:
        manifest = evidence_manifest()
        manifest["execution_scenarios"][0]["external_effects"][0]["effect_id"] = "undeclared-effect"
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EXTERNAL_EFFECT_NOT_DECLARED", result.stderr)

    def test_candidate_freeze_binds_the_profile_digest(self) -> None:
        manifest = evidence_manifest()
        manifest["candidate_freeze"]["project_profile_sha256"] = "stale"
        result = self.validate(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PROJECT_PROFILE_DIGEST_MISMATCH", result.stderr)


class CompletionReceiptTests(unittest.TestCase):
    def test_receipt_revalidates_every_input_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate.json"
            candidate.write_text('{"candidate_commit":"abc123"}\n', encoding="utf-8")
            receipt = root / "completion-receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "status": "ready",
                        "candidate_commit": "abc123",
                        "issued_at": "2026-08-05T00:00:00Z",
                        "inputs": {
                            "candidate_evidence": {
                                "path": str(candidate),
                                "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = run_script("scripts/validate_completion_receipt.py", str(receipt))
            self.assertEqual(result.returncode, 0, result.stderr)

            candidate.write_text('{"candidate_commit":"changed"}\n', encoding="utf-8")
            result = run_script("scripts/validate_completion_receipt.py", str(receipt))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("COMPLETION_RECEIPT_INPUT_CHANGED", result.stderr)

    def test_terminal_state_digest_survives_only_the_completion_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "program-state.yaml"
            state.write_text(
                """schema_version: "1.2"
status: PROGRAM_TARGET_VERIFIED
runtime_goal:
  status: active
candidate:
  commit: "abc123"
completion_receipt:
  status: pending
  path: ""
  sha256: ""
""",
                encoding="utf-8",
            )
            receipt = root / "completion-receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "status": "ready",
                        "candidate_commit": "abc123",
                        "issued_at": "2026-08-05T00:00:00Z",
                        "inputs": {
                            "program_state": {
                                "path": str(state),
                                "sha256": file_digest(state, "terminal_state"),
                                "digest_mode": "terminal_state",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            state.write_text(
                state.read_text(encoding="utf-8")
                .replace("PROGRAM_TARGET_VERIFIED", "COMPLETE")
                .replace("status: active", "status: complete")
                .replace("status: pending", "status: ready")
                .replace('path: ""', 'path: "completion-receipt.json"')
                .replace('sha256: ""', 'sha256: "receipt-digest"'),
                encoding="utf-8",
            )
            result = run_script("scripts/validate_completion_receipt.py", str(receipt))
            self.assertEqual(result.returncode, 0, result.stderr)

            state.write_text(
                state.read_text(encoding="utf-8").replace('commit: "abc123"', 'commit: "changed"'),
                encoding="utf-8",
            )
            result = run_script("scripts/validate_completion_receipt.py", str(receipt))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("COMPLETION_RECEIPT_INPUT_CHANGED", result.stderr)

    def test_state_templates_expose_profile_and_receipt_contracts(self) -> None:
        delivery = (
            PLUGIN_ROOT
            / "skills/goal-driven-delivery/assets/delivery-state-template.yaml"
        ).read_text(encoding="utf-8")
        program = (
            PLUGIN_ROOT
            / "skills/product-to-delivery/assets/program-state-template.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("project_profile_path:", delivery)
        self.assertIn("completion_receipt:", delivery)
        self.assertIn("completion_receipt:", program)


class RoutingRecorderTests(unittest.TestCase):
    @staticmethod
    def recoverable_record() -> dict[str, object]:
        return {
            "thread_id": "implementation-thread",
            "turn_id": "implementation-turn",
            "task_class": "implementation",
            "requested_model": "gpt-5.6-terra",
            "request_explicit": True,
            "observed_model": "gpt-5.6-terra",
            "observed_source": "rollout.turn_context.payload.model",
            "phase": "execution",
            "verified": True,
            "allowed_reason": "implementation",
        }

    @staticmethod
    def write_runtime_turn(sessions: Path, model: str) -> None:
        (sessions / "rollout-implementation-thread.jsonl").write_text(
            json.dumps(
                {
                    "type": "turn_context",
                    "payload": {
                        "turn_id": "implementation-turn",
                        "model": model,
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def test_invalid_event_never_mutates_the_routing_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "model-routing.jsonl"
            event = root / "event.json"
            record = {
                "thread_id": "canary-thread",
                "turn_id": "canary-turn",
                "task_class": "routing_canary",
                "requested_model": "gpt-5.6-terra",
                "request_explicit": True,
                "observed_model": "gpt-5.6-terra",
                "observed_source": "rollout.turn_context.payload.model",
                "phase": "initial",
                "verified": True,
                "allowed_reason": "routing_canary",
            }
            event.write_text(json.dumps(record), encoding="utf-8")
            result = run_script(
                "scripts/append_routing_event.py",
                "--log",
                str(log),
                "--event",
                str(event),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            accepted = log.read_text(encoding="utf-8")

            record["turn_id"] = "bad-turn"
            record["task_class"] = "project_specific_special_case"
            event.write_text(json.dumps(record), encoding="utf-8")
            result = run_script(
                "scripts/append_routing_event.py",
                "--log",
                str(log),
                "--event",
                str(event),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(log.read_text(encoding="utf-8"), accepted)

    def test_empty_routing_log_recovers_only_with_raw_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            source = root / "recovery.jsonl"
            source.write_text(
                json.dumps(self.recoverable_record()) + "\n",
                encoding="utf-8",
            )
            self.write_runtime_turn(sessions, "gpt-5.6-terra")
            log = root / "model-routing.jsonl"
            log.write_text("", encoding="utf-8")

            result = run_script(
                "scripts/recover_model_routing.py",
                "--log",
                str(log),
                "--source",
                str(source),
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            recovered = [
                json.loads(line)
                for line in log.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(recovered, [self.recoverable_record()])

    def test_failed_routing_recovery_leaves_empty_log_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            source = root / "recovery.jsonl"
            source.write_text(
                json.dumps(self.recoverable_record()) + "\n",
                encoding="utf-8",
            )
            self.write_runtime_turn(sessions, "gpt-5.6-sol")
            log = root / "model-routing.jsonl"
            log.write_text("\n", encoding="utf-8")

            result = run_script(
                "scripts/recover_model_routing.py",
                "--log",
                str(log),
                "--source",
                str(source),
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ROUTING_RECOVERY_RAW_EVIDENCE_REQUIRED", result.stderr)
            self.assertEqual(log.read_text(encoding="utf-8"), "\n")

    def test_routing_recovery_never_overwrites_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "model-routing.jsonl"
            log.write_text('{"existing":true}\n', encoding="utf-8")
            source = root / "recovery.jsonl"
            source.write_text(
                json.dumps(self.recoverable_record()) + "\n",
                encoding="utf-8",
            )

            result = run_script(
                "scripts/recover_model_routing.py",
                "--log",
                str(log),
                "--source",
                str(source),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ROUTING_RECOVERY_REQUIRES_EMPTY_LOG", result.stderr)
            self.assertEqual(log.read_text(encoding="utf-8"), '{"existing":true}\n')

    def test_routing_recovery_rejects_a_non_file_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "model-routing.jsonl"
            log.mkdir()
            source = root / "recovery.jsonl"
            source.write_text(
                json.dumps(self.recoverable_record()) + "\n",
                encoding="utf-8",
            )

            result = run_script(
                "scripts/recover_model_routing.py",
                "--log",
                str(log),
                "--source",
                str(source),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ROUTING_RECOVERY_LOG_NOT_REGULAR_FILE", result.stderr)
            self.assertTrue(log.is_dir())

    def test_completion_ready_recovery_rejects_a_partial_route_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            source = root / "recovery.jsonl"
            source.write_text(
                json.dumps(self.recoverable_record()) + "\n",
                encoding="utf-8",
            )
            self.write_runtime_turn(sessions, "gpt-5.6-terra")
            log = root / "model-routing.jsonl"

            result = run_script(
                "scripts/recover_model_routing.py",
                "--log",
                str(log),
                "--source",
                str(source),
                "--sessions-root",
                str(sessions),
                "--archived-root",
                str(root / "archived"),
                "--completion-ready",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MODEL_CANARY_INCOMPLETE", result.stderr)
            self.assertFalse(log.exists())


if __name__ == "__main__":
    unittest.main()
