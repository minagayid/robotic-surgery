import tempfile
import unittest
from pathlib import Path

from robotic_os import (
    DEFAULT_WORKCELL_PROFILE,
    FaultInjector,
    IndependentSafetyController,
    MotionProposal,
    RobotState,
    SafetyLimits,
    TelemetryRecord,
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


if __name__ == "__main__":
    unittest.main()
