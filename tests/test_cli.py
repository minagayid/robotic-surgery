from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from robotic_surgery.cli import main


class CliTests(unittest.TestCase):
    def test_demo_command_emits_machine_readable_local_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["demo", "--journal", str(Path(temp_dir) / "events.jsonl"), "--json"])
        self.assertEqual(exit_code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["mode"], "simulation_only")

    def test_five_heart_demo_command_emits_orchestration_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["five-heart-demo", "--journal", str(Path(temp_dir) / "events.jsonl"), "--json"])
        self.assertEqual(exit_code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["orchestration"]["status"], "approved")

    def test_mechanics_demo_emits_units_assumptions_and_joint_loads(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["mechanics-demo", "--force-n", "0", "10", "--json"])
        self.assertEqual(exit_code, 0)
        result = json.loads(output.getvalue())
        self.assertAlmostEqual(result["joint_torques_nm"][0], 3.8)
        self.assertAlmostEqual(result["joint_torques_nm"][1], 1.8)
        self.assertIn(
            "gravity, inertia, friction, compliance, and contact uncertainty omitted",
            result["assumptions"],
        )

    def test_learning_subcommands_are_reachable_through_main_cli(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["learning", "sources"])
        self.assertEqual(exit_code, 0)
        self.assertIn("mock references only", output.getvalue())


if __name__ == "__main__":
    unittest.main()
