from __future__ import annotations

import math
import unittest

from robotic_surgery.contracts import MotionProposal, RobotState


class ContractTests(unittest.TestCase):
    def make_proposal(self, **overrides):
        values = {
            "source_id": "planner",
            "sequence": 1,
            "calibration_id": "cal-1",
            "created_at_ns": 1_000,
            "expires_at_ns": 2_000,
            "duration_ms": 100,
            "target_positions": (0.1, -0.1),
            "velocities": (0.5, 0.5),
            "force_limits_n": (2.0, 2.0),
        }
        values.update(overrides)
        return MotionProposal(**values)

    def test_motion_proposal_round_trips_as_json_data(self) -> None:
        proposal = self.make_proposal()
        restored = MotionProposal.from_dict(proposal.to_dict())
        self.assertEqual(restored, proposal)

    def test_motion_proposal_rejects_non_finite_values(self) -> None:
        with self.assertRaises(ValueError):
            self.make_proposal(target_positions=(math.nan, 0.0))

    def test_motion_proposal_rejects_unknown_schema(self) -> None:
        with self.assertRaises(ValueError):
            self.make_proposal(schema_version=999)

    def test_robot_state_rejects_mismatched_joint_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            RobotState(
                timestamp_ns=1_000,
                calibration_id="cal-1",
                joint_positions=(0.0, 0.0),
                heartbeat_seq=1,
                proximity_m=1.0,
                sensor_health=(True,),
            )

    def test_robot_state_rejects_string_sensor_health(self) -> None:
        with self.assertRaises(ValueError):
            RobotState(
                timestamp_ns=1_000,
                calibration_id="cal-1",
                joint_positions=(0.0,),
                heartbeat_seq=1,
                proximity_m=1.0,
                sensor_health=("false",),
            )


if __name__ == "__main__":
    unittest.main()
