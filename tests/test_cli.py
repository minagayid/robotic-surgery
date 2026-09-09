from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from robotic_os.cli import main


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


if __name__ == "__main__":
    unittest.main()
