from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from robotic_os.benchmark import run_benchmark
from robotic_os.scenarios import run_demo, run_five_heart_demo


class ScenarioTests(unittest.TestCase):
    def test_demo_exercises_approval_clamp_and_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_demo(Path(temp_dir) / "demo.jsonl")
        self.assertEqual(result["mode"], "simulation_only")
        self.assertEqual([step["status"] for step in result["steps"]], ["approved", "clamped", "rejected"])
        self.assertTrue(result["journal_verified"])

    def test_benchmark_reports_deterministic_decision_counts(self) -> None:
        result = run_benchmark(iterations=50)
        self.assertEqual(result["iterations"], 50)
        self.assertEqual(result["approved"], 50)
        self.assertGreaterEqual(result["p99_us"], result["p50_us"])

    def test_five_heart_demo_runs_wave_gated_atomic_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_five_heart_demo(Path(temp_dir) / "five-heart.jsonl")
        self.assertEqual(result["orchestration"]["status"], "approved")
        self.assertEqual(len(result["orchestration"]["processor_decisions"]), 4)
        self.assertEqual(len(result["orchestration"]["coordinator_decisions"]), 2)
        self.assertEqual(result["spatial_snapshot"]["status"], "clear")
        self.assertTrue(result["journal_verified"])


if __name__ == "__main__":
    unittest.main()
