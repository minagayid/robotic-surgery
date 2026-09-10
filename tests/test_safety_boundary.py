import tempfile
import unittest
from pathlib import Path

from robotic_os import (
    AdapterUnavailable,
    CalibrationManifest,
    CalibrationRegistry,
    DEFAULT_WORKCELL_PROFILE,
    FaultInjector,
    IndependentSafetyController,
    MotionProposal,
    RobotState,
    ROS2AdapterContract,
    SafetyLimits,
    SimulationActuatorAdapter,
    TelemetryRecord,
    append_jsonl,
    read_jsonl,
    IsolatedSafetyBoundary,
    run_soak,
    evaluate_release,
)
from robotic_os.clock import DeterministicClock
from robotic_os.events import EventJournal
from robotic_os.runtime import OfflineRuntime


class SafetyBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = DeterministicClock(1_000_000_000)
        self.limits = SafetyLimits(
            position_limits=((-1.0, 1.0), (-1.0, 1.0)),
            max_velocity=(1.0, 1.0),
            max_force_n=(5.0, 5.0),
            min_proximity_m=0.2,
            max_command_duration_ms=500,
        )
        self.state = RobotState(
            timestamp_ns=self.clock.now_ns(),
            calibration_id="cal-1",
            joint_positions=(0.0, 0.0),
            heartbeat_seq=1,
            proximity_m=1.0,
            sensor_health=(True, True),
        )

    def proposal(self, **overrides) -> MotionProposal:
        values = {
            "source_id": "planner",
            "sequence": 1,
            "calibration_id": "cal-1",
            "created_at_ns": self.clock.now_ns() - 1,
            "expires_at_ns": self.clock.now_ns() + 1_000_000_000,
            "duration_ms": 100,
            "target_positions": (0.1, -0.1),
            "velocities": (0.5, 0.5),
            "force_limits_n": (2.0, 2.0),
        }
        values.update(overrides)
        return MotionProposal(**values)

    def test_workcell_is_concrete_and_declares_safe_boundary(self) -> None:
        self.assertEqual(DEFAULT_WORKCELL_PROFILE.profile_id, "robotx-reference-four-extremity-v1")
        self.assertEqual(DEFAULT_WORKCELL_PROFILE.mode, "simulation_only")
        self.assertIn("no_hardware", DEFAULT_WORKCELL_PROFILE.actuation_policy)
        self.assertEqual(DEFAULT_WORKCELL_PROFILE.joint_count, 8)

    def test_independent_gate_rejects_injected_position_fault(self) -> None:
        gate = IndependentSafetyController(limits=self.limits, heartbeat_timeout_ns=100_000_000)
        decision = gate.authorize(self.proposal(target_positions=(2.0, 0.0)), self.state, now_ns=self.clock.now_ns())
        self.assertEqual(decision.status, "rejected")
        self.assertIn("independent_joint_0_position_limit", decision.reasons)

    def test_fault_injection_catches_stale_and_unhealthy_state(self) -> None:
        gate = IndependentSafetyController(limits=self.limits, heartbeat_timeout_ns=100_000_000)
        stale = FaultInjector.stale_heartbeat(self.state, now_ns=self.clock.now_ns(), timeout_ns=100_000_000)
        self.assertIn("independent_stale_heartbeat", gate.authorize(self.proposal(), stale, now_ns=self.clock.now_ns()).reasons)
        unhealthy = FaultInjector.unhealthy_sensor(self.state)
        self.assertIn("independent_sensor_unhealthy", gate.authorize(self.proposal(), unhealthy, now_ns=self.clock.now_ns()).reasons)

    def test_runtime_records_final_gate_and_blocks_emergency_stop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = OfflineRuntime(
                clock=self.clock,
                limits=self.limits,
                allowed_sources={"planner"},
                journal=EventJournal(Path(directory) / "events.jsonl"),
            )
            runtime.update_state(self.state)
            self.assertEqual(runtime.submit(self.proposal()).status, "approved")
            runtime.trigger_emergency_stop()
            stopped = runtime.submit(self.proposal(sequence=2))
            self.assertEqual(stopped.status, "stopped")
            self.assertTrue(runtime.journal.verify())

    def test_telemetry_round_trip_is_versioned(self) -> None:
        record = TelemetryRecord(
            event_type="state",
            timestamp_ns=10,
            source_id="robotx.offline-runtime",
            calibration_id="cal-1",
            safety_status="ready",
            payload={"joint_positions": [0.0, 0.1]},
            record_id="record-1",
        )
        self.assertEqual(TelemetryRecord.from_dict(record.to_dict()), record)

    def test_telemetry_jsonl_round_trip_is_replayable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "telemetry.jsonl"
            record = TelemetryRecord(
                event_type="decision",
                timestamp_ns=11,
                source_id="robotx.offline-runtime",
                calibration_id="cal-1",
                safety_status="approved",
                payload={"status": "approved"},
                record_id="record-2",
            )
            append_jsonl(path, record)
            self.assertEqual(read_jsonl(path), (record,))

    def test_calibration_registry_is_expiry_and_dimension_aware(self) -> None:
        manifest = CalibrationManifest.create(
            calibration_id="cal-1",
            robot_model="robotx-fixture",
            joint_count=2,
            coordinate_frames=("base", "tool"),
            created_at_ns=900_000_000,
            expires_at_ns=2_000_000_000,
            source="test-fixture",
        )
        registry = CalibrationRegistry([manifest])
        self.assertEqual(registry.require("cal-1", joint_count=2, now_ns=self.clock.now_ns()), manifest)
        with self.assertRaises(ValueError):
            registry.require("cal-1", joint_count=3, now_ns=self.clock.now_ns())
        with self.assertRaises(ValueError):
            registry.require("cal-1", joint_count=2, now_ns=2_000_000_000)

    def test_actuator_boundary_is_simulation_only_and_ros_contract_fails_closed(self) -> None:
        simulation = SimulationActuatorAdapter().apply(self.proposal(), now_ns=self.clock.now_ns())
        self.assertTrue(simulation.accepted)
        self.assertFalse(simulation.external_action)
        ros = ROS2AdapterContract({"command": "/robotx/command"})
        self.assertEqual(ros.build_message(self.proposal())["topics"]["command"], "/robotx/command")
        with self.assertRaises(AdapterUnavailable):
            ros.apply(self.proposal(), now_ns=self.clock.now_ns())

    def test_runtime_does_not_advance_state_when_adapter_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = OfflineRuntime(
                clock=self.clock,
                limits=self.limits,
                allowed_sources={"planner"},
                journal=EventJournal(Path(directory) / "events.jsonl"),
                actuator=ROS2AdapterContract(),
            )
            runtime.update_state(self.state)
            decision = runtime.submit(self.proposal())
            self.assertEqual(decision.status, "stopped")
            self.assertIn("actuator_adapter_unavailable", decision.reasons)
            self.assertEqual(runtime.state.joint_positions, self.state.joint_positions)

    def test_isolated_safety_worker_approves_safe_proposal(self) -> None:
        boundary = IsolatedSafetyBoundary(
            limits=self.limits,
            heartbeat_timeout_ns=100_000_000,
            timeout_ms=2_000,
        )
        decision = boundary.authorize(self.proposal(), self.state, now_ns=self.clock.now_ns())
        self.assertEqual(decision.status, "approved")

    def test_soak_harness_catches_periodic_faults(self) -> None:
        report = run_soak(iterations=100, fault_interval=25)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["fault_rejected"], 4)
        self.assertEqual(report["unexpected"], 0)
        self.assertFalse(report["external_actuation"])

    def test_release_gate_blocks_missing_physical_evidence(self) -> None:
        report = evaluate_release({})
        self.assertEqual(report.status, "blocked")
        self.assertFalse(report.production_approved)
        self.assertTrue(any(not check.passed for check in report.checks))

    def test_release_gate_accepts_only_complete_evidence_for_review(self) -> None:
        soak = run_soak(iterations=100, fault_interval=25)
        manifest = {
            "target_hardware": "robotx-fixture-v1",
            "certified_safety_controller": {"certified": True, "certificate_id": "safety-cert-1"},
            "calibration": {"calibration_id": "cal-1", "checksum": "a" * 64, "approved_by": "calibration-authority"},
            "hardware_in_loop": {"passed": True, "independent_verification": True},
            "soak": soak,
            "independent_review": True,
            "checked_at_ns": 10,
        }
        report = evaluate_release(manifest, minimum_soak_iterations=100)
        self.assertEqual(report.status, "eligible_for_independent_production_review")
        self.assertFalse(report.production_approved)
        tampered = dict(soak)
        tampered["unexpected"] = 1
        manifest["soak"] = tampered
        self.assertEqual(evaluate_release(manifest, minimum_soak_iterations=100).status, "blocked")
        malformed = dict(manifest)
        malformed["soak"] = {"iterations": "not-a-number"}
        self.assertEqual(evaluate_release(malformed, minimum_soak_iterations=100).status, "blocked")


if __name__ == "__main__":
    unittest.main()
