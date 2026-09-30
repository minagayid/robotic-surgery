import unittest
from robotic_surgery.fault_benchmark import run_fault_benchmark


class FaultBenchmarkTests(unittest.TestCase):
    def test_all_faults_fail_closed_and_control_can_run(self):
        result = run_fault_benchmark()
        self.assertEqual(result["passed"], 8)
        self.assertEqual(result["external_actions"], [])
        for row in result["cases"][1:]:
            self.assertIn(row["decision"]["status"], {"rejected", "stopped"})
            self.assertTrue(all(v == 0 for v in row["decision"]["effective_velocities"]))
