from __future__ import annotations

import unittest

from robotic_surgery.contracts import SpatialObservation
from robotic_surgery.spatial import SpatialFusionEngine


class SpatialFusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SpatialFusionEngine(max_age_ns=100, min_confidence=0.75)

    def observation(self, *, modality: str, occupied: bool = False, confidence: float = 0.9, timestamp_ns: int = 1_000):
        return SpatialObservation(
            source_id=f"{modality}-1",
            modality=modality,
            region_id="workcell",
            timestamp_ns=timestamp_ns,
            calibration_id="cal-1",
            occupied=occupied,
            confidence=confidence,
        )

    def test_wave_modalities_can_clear_a_region_without_a_camera(self) -> None:
        snapshot = self.engine.fuse(
            [self.observation(modality="ultrasonic"), self.observation(modality="mmwave_radar")],
            now_ns=1_050,
            calibration_id="cal-1",
            region_id="workcell",
        )
        self.assertEqual(snapshot.status, "clear")
        self.assertFalse(snapshot.stop_required)
        self.assertEqual(set(snapshot.modality_ids), {"ultrasonic", "mmwave_radar"})

    def test_camera_only_evidence_remains_unknown(self) -> None:
        snapshot = self.engine.fuse(
            [self.observation(modality="rgb"), self.observation(modality="depth")],
            now_ns=1_050,
            calibration_id="cal-1",
            region_id="workcell",
        )
        self.assertEqual(snapshot.status, "unknown")
        self.assertTrue(snapshot.stop_required)
        self.assertIn("wave_evidence_required", snapshot.reasons)

    def test_contradiction_is_unknown_and_stop_required(self) -> None:
        snapshot = self.engine.fuse(
            [
                self.observation(modality="ultrasonic", occupied=True),
                self.observation(modality="mmwave_radar", occupied=False),
            ],
            now_ns=1_050,
            calibration_id="cal-1",
            region_id="workcell",
        )
        self.assertEqual(snapshot.status, "unknown")
        self.assertTrue(snapshot.conflict)
        self.assertTrue(snapshot.stop_required)

    def test_stale_evidence_cannot_clear_a_region(self) -> None:
        snapshot = self.engine.fuse(
            [self.observation(modality="ultrasonic", timestamp_ns=1_000)],
            now_ns=1_101,
            calibration_id="cal-1",
            region_id="workcell",
        )
        self.assertEqual(snapshot.status, "unknown")
        self.assertIn("stale_observation", snapshot.reasons)

    def test_weak_modality_prevents_a_clear_decision(self) -> None:
        snapshot = self.engine.fuse(
            [
                self.observation(modality="ultrasonic", confidence=0.9),
                self.observation(modality="mmwave_radar", confidence=0.4),
            ],
            now_ns=1_050,
            calibration_id="cal-1",
            region_id="workcell",
        )
        self.assertEqual(snapshot.status, "unknown")
        self.assertTrue(snapshot.stop_required)
        self.assertIn("clear_confidence_below_threshold", snapshot.reasons)


if __name__ == "__main__":
    unittest.main()
