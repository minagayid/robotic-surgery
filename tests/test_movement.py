from __future__ import annotations

import unittest

from robotic_os.contracts import MotionProposal, RobotState, SafetyLimits, SpatialObservation
from robotic_os.movement import EXTREMITY_PROCESSORS, ExtremityProcessor, FiveHeartOrchestrator
from robotic_os.spatial import SpatialFusionEngine


class FiveHeartOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = RobotState(
            timestamp_ns=1_000,
            calibration_id="cal-1",
            joint_positions=(0.0,) * 8,
            heartbeat_seq=1,
            proximity_m=1.0,
            sensor_health=(True,) * 8,
        )
        processors = {}
        for offset, name in enumerate(EXTREMITY_PROCESSORS):
            processors[name] = ExtremityProcessor(
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
        self.orchestrator = FiveHeartOrchestrator(processors)
        self.snapshot = SpatialFusionEngine().fuse(
            [
                self.observation("ultrasonic"),
                self.observation("mmwave_radar"),
            ],
            now_ns=1_000,
            calibration_id="cal-1",
            region_id="workcell",
        )

    @staticmethod
    def observation(modality: str):
        from robotic_os.contracts import SpatialObservation

        return SpatialObservation(
            source_id=f"{modality}-1",
            modality=modality,
            region_id="workcell",
            timestamp_ns=1_000,
            calibration_id="cal-1",
            occupied=False,
            confidence=0.9,
        )

    def proposals(self, orchestration_id: str = "bundle-1"):
        return {
            name: MotionProposal(
                source_id=f"planner.{name}",
                sequence=1,
                calibration_id="cal-1",
                created_at_ns=999,
                expires_at_ns=200_000_000,
                duration_ms=100,
                target_positions=(0.1, -0.1),
                velocities=(0.5, 0.5),
                force_limits_n=(2.0, 2.0),
                actuator_group=name,
                orchestration_id=orchestration_id,
            )
            for name in EXTREMITY_PROCESSORS
        }

    def test_all_four_processors_and_orchestrator_admit_atomically(self) -> None:
        decision = self.orchestrator.orchestrate(
            self.proposals(), self.state, spatial_snapshot=self.snapshot, now_ns=1_000
        )
        self.assertEqual(decision.status, "approved")
        self.assertEqual(len(decision.processor_decisions), 4)
        self.assertEqual(decision.effective_target_positions, (0.1, -0.1) * 4)
        self.assertEqual(
            [(item.coordinator_id, item.status) for item in decision.coordinator_decisions],
            [("upper_coordinating_processor", "approved"), ("lower_coordinating_processor", "approved")],
        )

    def test_missing_extremity_is_rejected_by_final_processor(self) -> None:
        proposals = self.proposals()
        proposals.pop("right_leg")
        decision = self.orchestrator.orchestrate(
            proposals, self.state, spatial_snapshot=self.snapshot, now_ns=1_000
        )
        self.assertEqual(decision.status, "rejected")
        self.assertIn("missing_processor:right_leg", decision.reasons)

    def test_one_extremity_failure_blocks_the_whole_bundle(self) -> None:
        proposals = self.proposals()
        proposals["left_arm"] = MotionProposal(
            **{**proposals["left_arm"].to_dict(), "target_positions": [2.0, 0.0]}
        )
        decision = self.orchestrator.orchestrate(
            proposals, self.state, spatial_snapshot=self.snapshot, now_ns=1_000
        )
        self.assertEqual(decision.status, "rejected")
        self.assertTrue(any("left_arm:joint_0_position_limit" in reason for reason in decision.reasons))
        regional = {item.coordinator_id: item for item in decision.coordinator_decisions}
        self.assertEqual(regional["upper_coordinating_processor"].status, "rejected")
        self.assertEqual(regional["lower_coordinating_processor"].status, "approved")

    def test_conflicting_spatial_evidence_stops_before_regional_commit(self) -> None:
        conflicting = SpatialFusionEngine().fuse(
            [
                self.observation("ultrasonic"),
                SpatialObservation(
                    source_id="mmwave-radar-1",
                    modality="mmwave_radar",
                    region_id="workcell",
                    timestamp_ns=1_000,
                    calibration_id="cal-1",
                    occupied=True,
                    confidence=0.95,
                ),
            ],
            now_ns=1_000,
            calibration_id="cal-1",
            region_id="workcell",
        )
        decision = self.orchestrator.orchestrate(
            self.proposals("fault-conflict"), self.state, spatial_snapshot=conflicting, now_ns=1_000
        )
        self.assertEqual(decision.status, "rejected")
        self.assertIn("spatial_evidence_conflict", decision.reasons)
        self.assertEqual(decision.coordinator_decisions, ())

    def test_replayed_orchestration_is_rejected(self) -> None:
        proposals = self.proposals()
        first = self.orchestrator.orchestrate(
            proposals, self.state, spatial_snapshot=self.snapshot, now_ns=1_000
        )
        second = self.orchestrator.orchestrate(
            proposals, self.state, spatial_snapshot=self.snapshot, now_ns=1_000
        )
        self.assertEqual(first.status, "approved")
        self.assertEqual(second.status, "rejected")
        self.assertIn("replayed_orchestration", second.reasons)


if __name__ == "__main__":
    unittest.main()
