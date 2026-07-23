from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from robotx_os.actuator import SimulatedVelocityActuator
from robotx_os.clock import ManualClock
from robotx_os.contracts import (
    BodyState,
    ContractHeader,
    HealthSnapshot,
    MotionProposal,
    SafetyAction,
    SafetyLimits,
)
from robotx_os.events import EventJournal, read_verified_events
from robotx_os.runtime import RobotRuntime
from robotx_os.safety import SafetySupervisor


class RuntimeAndJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temporary_directory.name) / "events.jsonl"
        self.clock = ManualClock(5_000_000_000)
        calibration = "cal-v1"
        limits = SafetyLimits(
            calibration_id=calibration,
            authorized_motion_sources=("test",),
            authorized_state_sources=("test",),
            joint_position_min=(-1.0,),
            joint_position_max=(1.0,),
            max_joint_velocity=(0.25,),
            max_joint_effort=(5.0,),
        )
        self.runtime = RobotRuntime(
            self.clock,
            SafetySupervisor(limits),
            SimulatedVelocityActuator(),
            EventJournal(self.log_path, sync_writes=False),
        )
        self.header = ContractHeader(self.clock.now_ns(), "test", calibration, 1)
        self.state = BodyState(self.header, (0.0,), (0.0,), (0.0,), 1.0, True)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_runtime_executes_only_approved_velocity_and_records_it(self) -> None:
        health = HealthSnapshot(
            self.clock.now_ns(), hardware_safety_ready=True, configuration_verified=True
        )
        motion = MotionProposal(
            self.header, "move-1", self.clock.now_ns() + 1_000_000_000, (0.2,),
            50_000_000,
        )
        decision, next_state = self.runtime.execute(motion, self.state, health)
        self.assertEqual(SafetyAction.APPROVE, decision.action)
        self.assertAlmostEqual(0.01, next_state.joint_positions[0])
        records = list(read_verified_events(self.log_path))
        self.assertEqual(1, len(records))
        self.assertEqual("approve", records[0]["payload"]["decision"]["action"])

    def test_stop_decision_forces_zero_velocity(self) -> None:
        health = HealthSnapshot(
            self.clock.now_ns(), physical_estop_engaged=True,
            hardware_safety_ready=True, configuration_verified=True,
        )
        motion = MotionProposal(
            self.header, "move-1", self.clock.now_ns() + 1_000_000, (0.2,),
            1_000_000,
        )
        decision, next_state = self.runtime.execute(motion, self.state, health)
        self.assertEqual(SafetyAction.STOP, decision.action)
        self.assertEqual((0.0,), next_state.joint_velocities)
        self.assertFalse(next_state.actuator_power_enabled)

    def test_journal_detects_tampering(self) -> None:
        journal = EventJournal(self.log_path, sync_writes=False)
        journal.append("test", self.clock.now_ns(), {"safe": True})
        record = json.loads(self.log_path.read_text(encoding="utf-8"))
        record["payload"]["safe"] = False
        self.log_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "integrity failure"):
            list(read_verified_events(self.log_path))


if __name__ == "__main__":
    unittest.main()
