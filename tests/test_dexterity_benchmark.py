from __future__ import annotations

import math
import unittest
from dataclasses import replace

from robotic_surgery.dexterity_benchmark import (
    DexterityTrial,
    TactileFrame,
    evaluate_trials,
)


def frame(
    *,
    sensor_id: str = "taxel-array-1",
    timestamp_ns: int = 1_000,
    sequence: int = 1,
    force_n: tuple[float, float, float] = (0.0, 0.0, 2.0),
) -> TactileFrame:
    return TactileFrame(
        sensor_id=sensor_id,
        sensor_model="research-array",
        timestamp_ns=timestamp_ns,
        sequence=sequence,
        calibration_id="cal-2026-01",
        coordinate_frame="tool0",
        force_n=force_n,
        torque_nm=(0.0, 0.0, 0.1),
        force_uncertainty_n=(0.1, 0.1, 0.2),
        torque_uncertainty_nm=(0.01, 0.01, 0.02),
        contact_probability=0.95,
    )


def trial(
    trial_id: str,
    *,
    success: bool,
    duration_ns: int = 2_000_000_000,
    interventions: int = 0,
    drops: int = 0,
    forces: tuple[tuple[float, float, float], ...] = ((0.0, 0.0, 2.0),),
) -> DexterityTrial:
    samples = tuple(
        frame(timestamp_ns=1_000 + i, sequence=i, force_n=force)
        for i, force in enumerate(forces, start=1)
    )
    return DexterityTrial(
        trial_id=trial_id,
        task_id="peg-transfer-v1",
        platform_id="platform-a",
        started_at_ns=1_000,
        finished_at_ns=1_000 + duration_ns,
        success=success,
        operator_interventions=interventions,
        dropped_objects=drops,
        tactile_frames=samples,
    )


class TactileFrameTests(unittest.TestCase):
    def test_tactile_record_round_trips_with_explicit_si_units(self) -> None:
        original = frame()
        record = original.to_record()
        restored = TactileFrame.from_record(record)

        self.assertEqual(restored, original)
        self.assertEqual(record["schema_version"], "0.1.0")
        self.assertEqual(record["units"]["force"], "N")
        self.assertEqual(record["units"]["torque"], "N*m")
        self.assertEqual(record["units"]["time"], "ns")

    def test_rejects_non_finite_force_and_negative_uncertainty(self) -> None:
        with self.assertRaises(ValueError):
            frame(force_n=(math.nan, 0.0, 0.0))
        with self.assertRaises(ValueError):
            TactileFrame(
                sensor_id="sensor",
                sensor_model="model",
                timestamp_ns=0,
                sequence=0,
                calibration_id="cal",
                coordinate_frame="tool0",
                force_n=(0.0, 0.0, 0.0),
                torque_nm=(0.0, 0.0, 0.0),
                force_uncertainty_n=(-0.1, 0.0, 0.0),
                torque_uncertainty_nm=(0.0, 0.0, 0.0),
                contact_probability=0.5,
            )

    def test_rejects_unknown_schema_or_non_si_unit(self) -> None:
        record = frame().to_record()
        record["schema_version"] = "9.9.9"
        with self.assertRaises(ValueError):
            TactileFrame.from_record(record)

        record = frame().to_record()
        record["units"]["force"] = "kg"
        with self.assertRaises(ValueError):
            TactileFrame.from_record(record)


class DexterityTrialTests(unittest.TestCase):
    def test_rejects_non_monotonic_sensor_sequences(self) -> None:
        first = frame(timestamp_ns=1_100, sequence=2)
        second = frame(timestamp_ns=1_101, sequence=1)
        with self.assertRaises(ValueError):
            DexterityTrial(
                trial_id="trial-1",
                task_id="peg-transfer-v1",
                platform_id="platform-a",
                started_at_ns=1_000,
                finished_at_ns=2_000,
                success=True,
                operator_interventions=0,
                dropped_objects=0,
                tactile_frames=(first, second),
            )

    def test_rejects_frames_outside_trial_window(self) -> None:
        with self.assertRaises(ValueError):
            DexterityTrial(
                trial_id="trial-1",
                task_id="peg-transfer-v1",
                platform_id="platform-a",
                started_at_ns=1_000,
                finished_at_ns=2_000,
                success=True,
                operator_interventions=0,
                dropped_objects=0,
                tactile_frames=(frame(timestamp_ns=2_001),),
            )


class BenchmarkEvaluationTests(unittest.TestCase):
    def test_reports_repeatable_core_metrics(self) -> None:
        trials = (
            trial("t1", success=True, duration_ns=2_000_000_000, forces=((0, 0, 2), (0, 0, 4))),
            trial("t2", success=False, duration_ns=4_000_000_000, interventions=1, drops=1),
            trial("t3", success=True, duration_ns=3_000_000_000),
        )
        result = evaluate_trials(trials, force_limit_n=3.0)

        self.assertEqual(result.trial_count, 3)
        self.assertEqual(result.success_count, 2)
        self.assertAlmostEqual(result.success_rate, 2 / 3)
        self.assertAlmostEqual(result.median_duration_s, 3.0)
        self.assertAlmostEqual(result.mean_operator_interventions, 1 / 3)
        self.assertAlmostEqual(result.drop_rate, 1 / 3)
        self.assertEqual(result.tactile_frame_count, 4)
        self.assertEqual(result.force_limit_exceedance_count, 1)
        self.assertEqual(result.max_peak_force_n, 4.0)

    def test_rejects_mixed_tasks_and_duplicate_trials(self) -> None:
        first = trial("t1", success=True)
        second = trial("t2", success=True)
        second = replace(second, task_id="another-task")
        with self.assertRaises(ValueError):
            evaluate_trials((first, second))

        with self.assertRaises(ValueError):
            evaluate_trials((first, first))

    def test_requires_a_non_empty_trial_collection(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_trials(())


if __name__ == "__main__":
    unittest.main()
