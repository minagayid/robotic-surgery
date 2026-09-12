from __future__ import annotations

import unittest

from robotic_os.spatial_4d import SpatialMeasurement, SpatialRecognitionSystem


class SpatialRecognition4DTests(unittest.TestCase):
    def test_clear_requires_independent_wave_evidence(self) -> None:
        engine = SpatialRecognitionSystem(sector_count=2)
        measurements = []
        for sector in range(2):
            for modality, emits in (("rgb", False), ("mmwave_radar", True)):
                measurements.append(SpatialMeasurement(
                    source_id=f"{modality}-{sector}", modality=modality, region_id="demo",
                    sector_index=sector, timestamp_ns=1_000, calibration_id="demo-cal",
                    object_id=f"clear-{sector}", position=(0.0, 0.0, 0.0),
                    velocity=(0.0, 0.0, 0.0), confidence=0.9, occupied=False,
                    emits_energy=emits,
                ))
        snapshot = engine.fuse(measurements, now_ns=1_000,
                               calibration_id="demo-cal", region_id="demo")
        self.assertEqual(snapshot.status, "clear")
        self.assertFalse(snapshot.stop_required)
        self.assertEqual(snapshot.to_safety_snapshot().status, "clear")

    def test_demo_preserves_observed_and_inferred_motion(self) -> None:
        engine = SpatialRecognitionSystem(sector_count=16, prediction_horizon_s=2.0)
        snapshot = engine.fuse(
            engine.demo_measurements(),
            now_ns=1_000,
            calibration_id="demo-cal",
            region_id="demo",
        )
        self.assertEqual(snapshot.status, "occupied")
        self.assertEqual(snapshot.covered_sectors, tuple(range(16)))
        entities = {item.object_id: item for item in snapshot.entities}
        self.assertEqual(entities["person-3"].visibility, "observed")
        self.assertEqual(entities["occluded-target-10"].visibility, "inferred")
        self.assertEqual(entities["occluded-target-10"].predicted_position, (10.0, -0.4, 1.0))
        self.assertIn("mmwave_radar", snapshot.emission_modalities)

    def test_stale_and_disabled_emission_are_fail_closed(self) -> None:
        engine = SpatialRecognitionSystem(sector_count=2, max_age_ns=10, mode="eco")
        measurement = SpatialMeasurement(
            source_id="radar-1",
            modality="mmwave_radar",
            region_id="demo",
            sector_index=0,
            timestamp_ns=1,
            calibration_id="demo-cal",
            object_id="target",
            position=(1.0, 0.0, 0.0),
            velocity=(0.0, 0.0, 0.0),
            confidence=0.95,
            occupied=True,
            emits_energy=True,
        )
        disabled = SpatialMeasurement(
            **{**measurement.to_dict(), "source_id": "radar-2", "sector_index": 1,
               "timestamp_ns": 100}
        )
        snapshot = engine.fuse(
            [measurement, disabled], now_ns=100, calibration_id="demo-cal", region_id="demo"
        )
        self.assertEqual(snapshot.status, "unknown")
        self.assertTrue(snapshot.stop_required)
        self.assertIn("active_modality_disabled:mmwave_radar", snapshot.reasons)
        self.assertIn("stale_measurement", snapshot.reasons)
        self.assertEqual(snapshot.to_safety_snapshot().status, "unknown")

    def test_contradictory_track_is_unknown(self) -> None:
        engine = SpatialRecognitionSystem(sector_count=1)
        common = dict(
            region_id="demo",
            sector_index=0,
            timestamp_ns=1_000,
            calibration_id="demo-cal",
            object_id="same-target",
            position=(1.0, 0.0, 0.0),
            velocity=(0.0, 0.0, 0.0),
            confidence=0.9,
        )
        snapshot = engine.fuse(
            [
                SpatialMeasurement(source_id="rgb", modality="rgb", occupied=True, **common),
                SpatialMeasurement(
                    source_id="radar", modality="mmwave_radar", occupied=False,
                    emits_energy=True, **common,
                ),
            ],
            now_ns=1_000,
            calibration_id="demo-cal",
            region_id="demo",
        )
        self.assertEqual(snapshot.status, "unknown")
        self.assertTrue(snapshot.conflict)
        self.assertIn("contradictory_evidence:same-target", snapshot.reasons)


if __name__ == "__main__":
    unittest.main()
