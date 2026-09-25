from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from robotic_surgery.clock import DeterministicClock
from robotic_surgery.contracts import MotionProposal, RobotState, SafetyLimits, SpatialObservation
from robotic_surgery.events import EventJournal
from robotic_surgery.movement import EXTREMITY_PROCESSORS, ExtremityProcessor, FiveHeartOrchestrator
from robotic_surgery.runtime import OfflineRuntime
from robotic_surgery.spatial import SpatialFusionEngine


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

    def test_orchestrated_submit_honors_global_emergency_stop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            clock = DeterministicClock(1_000)
            runtime = OfflineRuntime(
                clock=clock,
                limits=SafetyLimits(
                    position_limits=((-1.0, 1.0),) * 8,
                    max_velocity=(1.0,) * 8,
                    max_force_n=(5.0,) * 8,
                    min_proximity_m=0.2,
                    max_command_duration_ms=500,
                ),
                allowed_sources={f"planner.{name}" for name in EXTREMITY_PROCESSORS},
                journal=EventJournal(Path(temp_dir) / "events.jsonl"),
            )
            runtime.update_state(
                RobotState(
                    timestamp_ns=clock.now_ns(),
                    calibration_id="cal-1",
                    joint_positions=(0.0,) * 8,
                    heartbeat_seq=1,
                    proximity_m=1.0,
                    sensor_health=(True,) * 8,
                )
            )
            processors = {
                name: ExtremityProcessor(
                    processor_id=name,
                    joint_indices=(offset * 2, offset * 2 + 1),
                    limits=SafetyLimits(
                        position_limits=((-1.0, 1.0), (-1.0, 1.0)),
                        max_velocity=(1.0, 1.0),
                        max_force_n=(5.0, 5.0),
                        min_proximity_m=0.2,
                        max_command_duration_ms=500,
                    ),
                    source_id=f"planner.{name}",
                )
                for offset, name in enumerate(EXTREMITY_PROCESSORS)
            }
            orchestrator = FiveHeartOrchestrator(processors)
            snapshot = SpatialFusionEngine().fuse(
                [
                    SpatialObservation("u", "ultrasonic", "workcell", 1_000, "cal-1", False, 0.9),
                    SpatialObservation("r", "mmwave_radar", "workcell", 1_000, "cal-1", False, 0.9),
                ],
                now_ns=1_000,
                calibration_id="cal-1",
                region_id="workcell",
            )
            proposals = {
                name: MotionProposal(
                    source_id=f"planner.{name}",
                    sequence=1,
                    calibration_id="cal-1",
                    created_at_ns=999,
                    expires_at_ns=1_000_001_000,
                    duration_ms=100,
                    target_positions=(0.1, -0.1),
                    velocities=(0.5, 0.5),
                    force_limits_n=(2.0, 2.0),
                    actuator_group=name,
                    orchestration_id="stop-test",
                )
                for name in EXTREMITY_PROCESSORS
            }
            runtime.trigger_emergency_stop()
            decision = runtime.submit_orchestrated(orchestrator, proposals, spatial_snapshot=snapshot)
            self.assertEqual(decision.status, "stopped")
            self.assertIn("emergency_stop_latched", decision.reasons)


if __name__ == "__main__":
    unittest.main()
