from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from robotic_os.clock import DeterministicClock
from robotic_os.contracts import MotionProposal, RobotState, SafetyLimits
from robotic_os.events import EventJournal
from robotic_os.runtime import OfflineRuntime


class RuntimeTests(unittest.TestCase):
    def make_runtime(self, temp_dir: str) -> OfflineRuntime:
        clock = DeterministicClock(1_000_000_000)
        limits = SafetyLimits(
            position_limits=((-1.0, 1.0), (-1.0, 1.0)),
            max_velocity=(1.0, 1.0),
            max_force_n=(5.0, 5.0),
            min_proximity_m=0.2,
            max_command_duration_ms=500,
        )
        runtime = OfflineRuntime(
            clock=clock,
            limits=limits,
            allowed_sources={"planner"},
            journal=EventJournal(Path(temp_dir) / "events.jsonl"),
        )
        runtime.update_state(
            RobotState(
                timestamp_ns=1_000_000_000,
                calibration_id="cal-1",
                joint_positions=(0.0, 0.0),
                heartbeat_seq=1,
                proximity_m=1.0,
                sensor_health=(True, True),
            )
        )
        return runtime

    def test_runtime_applies_only_approved_or_clamped_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = self.make_runtime(temp_dir)
            proposal = MotionProposal(
                source_id="planner",
                sequence=1,
                calibration_id="cal-1",
                created_at_ns=900_000_000,
                expires_at_ns=1_500_000_000,
                duration_ms=250,
                target_positions=(0.2, -0.2),
                velocities=(0.5, 0.5),
                force_limits_n=(2.0, 2.0),
            )
            decision = runtime.submit(proposal)
            self.assertEqual(decision.status, "approved")
            self.assertEqual(runtime.state.joint_positions, (0.2, -0.2))
            self.assertTrue(runtime.journal.verify())

    def test_runtime_stop_prevents_motion_until_reset_and_fresh_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = self.make_runtime(temp_dir)
            runtime.trigger_emergency_stop()
            proposal = MotionProposal(
                source_id="planner",
                sequence=1,
                calibration_id="cal-1",
                created_at_ns=900_000_000,
                expires_at_ns=1_500_000_000,
                duration_ms=100,
                target_positions=(0.2, -0.2),
                velocities=(0.5, 0.5),
                force_limits_n=(2.0, 2.0),
            )
            self.assertEqual(runtime.submit(proposal).status, "stopped")
            self.assertTrue(runtime.reset("operator-1"))
            self.assertEqual(runtime.submit(proposal).status, "rejected")


if __name__ == "__main__":
    unittest.main()
