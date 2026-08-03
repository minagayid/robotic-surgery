from __future__ import annotations

import unittest

from robotic_os.clock import DeterministicClock
from robotic_os.contracts import MotionProposal, RobotState, SafetyLimits
from robotic_os.safety import SafetySupervisor


class SafetySupervisorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = DeterministicClock(1_000_000_000)
        self.limits = SafetyLimits(
            position_limits=((-1.0, 1.0), (-1.0, 1.0)),
            max_velocity=(1.0, 1.0),
            max_force_n=(5.0, 5.0),
            min_proximity_m=0.2,
            max_command_duration_ms=500,
        )
        self.supervisor = SafetySupervisor(
            limits=self.limits,
            allowed_sources={"planner"},
            heartbeat_timeout_ns=200_000_000,
        )
        self.state = RobotState(
            timestamp_ns=1_000_000_000,
            calibration_id="cal-1",
            joint_positions=(0.0, 0.0),
            heartbeat_seq=1,
            proximity_m=1.0,
            sensor_health=(True, True),
        )

    def proposal(self, **overrides) -> MotionProposal:
        values = {
            "source_id": "planner",
            "sequence": 1,
            "calibration_id": "cal-1",
            "created_at_ns": 900_000_000,
            "expires_at_ns": 1_500_000_000,
            "duration_ms": 100,
            "target_positions": (0.1, -0.1),
            "velocities": (0.5, 0.5),
            "force_limits_n": (2.0, 2.0),
        }
        values.update(overrides)
        return MotionProposal(**values)

    def test_valid_proposal_is_approved(self) -> None:
        decision = self.supervisor.authorize(self.proposal(), self.state, now_ns=self.clock.now_ns())
        self.assertEqual(decision.status, "approved")
        self.assertEqual(decision.effective_velocities, (0.5, 0.5))

    def test_replayed_sequence_is_rejected(self) -> None:
        proposal = self.proposal()
        self.supervisor.authorize(proposal, self.state, now_ns=self.clock.now_ns())
        decision = self.supervisor.authorize(proposal, self.state, now_ns=self.clock.now_ns())
        self.assertEqual(decision.status, "rejected")
        self.assertIn("replayed_sequence", decision.reasons)

    def test_excess_velocity_is_clamped_without_raising_limits(self) -> None:
        decision = self.supervisor.authorize(
            self.proposal(velocities=(3.0, -4.0)), self.state, now_ns=self.clock.now_ns()
        )
        self.assertEqual(decision.status, "clamped")
        self.assertEqual(decision.effective_velocities, (1.0, -1.0))

    def test_expired_proposal_is_rejected(self) -> None:
        decision = self.supervisor.authorize(
            self.proposal(expires_at_ns=999_000_000), self.state, now_ns=self.clock.now_ns()
        )
        self.assertEqual(decision.status, "rejected")
        self.assertIn("expired", decision.reasons)

    def test_proposal_must_remain_valid_for_its_declared_duration(self) -> None:
        decision = self.supervisor.authorize(
            self.proposal(expires_at_ns=1_050_000_000, created_at_ns=900_000_000, duration_ms=100),
            RobotState(
                timestamp_ns=1_000_000_000,
                calibration_id="cal-1",
                joint_positions=(0.0, 0.0),
                heartbeat_seq=1,
                proximity_m=1.0,
                sensor_health=(True, True),
            ),
            now_ns=1_000_000_000,
        )
        self.assertEqual(decision.status, "rejected")
        self.assertIn("expiry_before_completion", decision.reasons)

    def test_stale_heartbeat_is_rejected(self) -> None:
        decision = self.supervisor.authorize(self.proposal(), self.state, now_ns=1_201_000_000)
        self.assertEqual(decision.status, "rejected")
        self.assertIn("stale_heartbeat", decision.reasons)

    def test_future_state_timestamp_is_rejected(self) -> None:
        future_state = RobotState(
            timestamp_ns=1_100_000_000,
            calibration_id="cal-1",
            joint_positions=(0.0, 0.0),
            heartbeat_seq=1,
            proximity_m=1.0,
            sensor_health=(True, True),
        )
        decision = self.supervisor.authorize(self.proposal(), future_state, now_ns=1_000_000_000)
        self.assertEqual(decision.status, "rejected")
        self.assertIn("future_state_timestamp", decision.reasons)

    def test_emergency_stop_latches_until_operator_reset(self) -> None:
        self.supervisor.trigger_emergency_stop()
        stopped = self.supervisor.authorize(self.proposal(), self.state, now_ns=self.clock.now_ns())
        self.assertEqual(stopped.status, "stopped")
        self.assertFalse(self.supervisor.reset(operator_id=""))
        self.assertTrue(self.supervisor.reset(operator_id="operator-1"))

    def test_unknown_source_and_calibration_are_rejected(self) -> None:
        decision = self.supervisor.authorize(
            self.proposal(source_id="unknown", calibration_id="other"),
            self.state,
            now_ns=self.clock.now_ns(),
        )
        self.assertEqual(decision.status, "rejected")
        self.assertIn("source_not_allowed", decision.reasons)
        self.assertIn("calibration_mismatch", decision.reasons)

    def test_unsafe_proximity_is_rejected(self) -> None:
        state = RobotState(
            timestamp_ns=1_000_000_000,
            calibration_id="cal-1",
            joint_positions=(0.0, 0.0),
            heartbeat_seq=1,
            proximity_m=0.1,
            sensor_health=(True, True),
        )
        decision = self.supervisor.authorize(self.proposal(), state, now_ns=self.clock.now_ns())
        self.assertEqual(decision.status, "rejected")
        self.assertIn("unsafe_proximity", decision.reasons)

    def test_proposal_and_state_dimensions_must_match(self) -> None:
        decision = self.supervisor.authorize(
            self.proposal(
                target_positions=(0.1, -0.1, 0.0),
                velocities=(0.5, 0.5, 0.5),
                force_limits_n=(2.0, 2.0, 2.0),
            ),
            self.state,
            now_ns=self.clock.now_ns(),
        )
        self.assertEqual(decision.status, "rejected")
        self.assertIn("joint_dimension_mismatch", decision.reasons)


if __name__ == "__main__":
    unittest.main()
