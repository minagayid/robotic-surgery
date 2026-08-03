from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from robotic_os.benchmark import run_benchmark
from robotic_os.scenarios import run_demo


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


if __name__ == "__main__":
    unittest.main()
