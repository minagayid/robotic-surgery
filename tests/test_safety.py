from __future__ import annotations

import math
import unittest

from robotx_os.contracts import (
    BodyState,
    ContractHeader,
    HealthSnapshot,
    MotionProposal,
    SafetyAction,
    SafetyLimits,
)
from robotx_os.safety import SafetySupervisor


NOW = 1_000_000_000
CALIBRATION = "test-cal-v1"


def limits() -> SafetyLimits:
    return SafetyLimits(
        calibration_id=CALIBRATION,
        authorized_motion_sources=("planner",),
        authorized_state_sources=("planner",),
        joint_position_min=(-2.0, -2.0),
        joint_position_max=(2.0, 2.0),
        max_joint_velocity=(0.5, 0.4),
        max_joint_effort=(10.0, 10.0),
    )


def header(*, sequence: int = 1, timestamp: int = NOW, confidence: float = 1.0) -> ContractHeader:
    return ContractHeader(timestamp, "planner", CALIBRATION, sequence, confidence)


def body(**changes: object) -> BodyState:
    values: dict[str, object] = {
        "header": header(),
        "joint_positions": (0.0, 0.0),
        "joint_velocities": (0.0, 0.0),
        "joint_efforts": (0.0, 0.0),
        "nearest_obstacle_m": 1.0,
        "actuator_power_enabled": True,
    }
    values.update(changes)
    return BodyState(**values)  # type: ignore[arg-type]


def proposal(*, sequence: int = 1, velocities: tuple[float, ...] = (0.1, 0.2), **changes: object) -> MotionProposal:
    values: dict[str, object] = {
        "header": header(sequence=sequence),
        "proposal_id": f"proposal-{sequence}",
        "valid_until_ns": NOW + 20_000_000,
        "target_joint_velocities": velocities,
        "execution_duration_ns": 10_000_000,
    }
    values.update(changes)
    return MotionProposal(**values)  # type: ignore[arg-type]


def health(**changes: object) -> HealthSnapshot:
    values: dict[str, object] = {
        "heartbeat_ns": NOW,
        "hardware_safety_ready": True,
        "configuration_verified": True,
    }
    values.update(changes)
    return HealthSnapshot(**values)  # type: ignore[arg-type]


class SafetySupervisorTests(unittest.TestCase):
    def test_approves_in_bounds_motion(self) -> None:
        decision = SafetySupervisor(limits()).evaluate(proposal(), body(), health(), NOW)
        self.assertEqual(SafetyAction.APPROVE, decision.action)
        self.assertEqual((0.1, 0.2), decision.approved_joint_velocities)

    def test_clamps_velocity_without_changing_limits(self) -> None:
        decision = SafetySupervisor(limits()).evaluate(
            proposal(velocities=(9.0, -9.0)), body(), health(), NOW
        )
        self.assertEqual(SafetyAction.CLAMP, decision.action)
        self.assertEqual((0.5, -0.4), decision.approved_joint_velocities)

    def test_expired_proposal_is_rejected_without_latching_stop(self) -> None:
        supervisor = SafetySupervisor(limits())
        decision = supervisor.evaluate(
            proposal(valid_until_ns=NOW - 1), body(), health(), NOW
        )
        self.assertEqual(SafetyAction.REJECT, decision.action)
        self.assertFalse(supervisor.stop_latched)

    def test_stale_heartbeat_stops_and_latches(self) -> None:
        supervisor = SafetySupervisor(limits())
        decision = supervisor.evaluate(
            proposal(), body(), health(heartbeat_ns=NOW - 100_000_001), NOW
        )
        self.assertEqual(SafetyAction.STOP, decision.action)
        self.assertEqual("heartbeat_stale", decision.reason)
        followup = supervisor.evaluate(proposal(sequence=2), body(), health(), NOW)
        self.assertEqual("stop_latched", followup.reason)

    def test_stop_reset_requires_deliberate_acknowledgement(self) -> None:
        supervisor = SafetySupervisor(limits())
        supervisor.evaluate(proposal(), body(nearest_obstacle_m=0.1), health(), NOW)
        self.assertFalse(
            supervisor.reset_stop(body(), health(), NOW, operator_acknowledged=False)
        )
        self.assertTrue(
            supervisor.reset_stop(body(), health(), NOW, operator_acknowledged=True)
        )
        self.assertFalse(supervisor.stop_latched)

    def test_replayed_sequence_is_rejected(self) -> None:
        supervisor = SafetySupervisor(limits())
        supervisor.evaluate(proposal(sequence=7), body(), health(), NOW)
        decision = supervisor.evaluate(proposal(sequence=7), body(), health(), NOW)
        self.assertEqual(SafetyAction.REJECT, decision.action)
        self.assertEqual("replayed_or_out_of_order", decision.reason)

    def test_non_finite_input_stops(self) -> None:
        decision = SafetySupervisor(limits()).evaluate(
            proposal(velocities=(math.nan, 0.0)), body(), health(), NOW
        )
        self.assertEqual(SafetyAction.STOP, decision.action)
        self.assertEqual("non_finite_numeric_input", decision.reason)

    def test_execution_must_fit_inside_expiry(self) -> None:
        decision = SafetySupervisor(limits()).evaluate(
            proposal(valid_until_ns=NOW + 1, execution_duration_ns=2), body(), health(), NOW
        )
        self.assertEqual(SafetyAction.REJECT, decision.action)
        self.assertEqual("execution_exceeds_expiry", decision.reason)

    def test_predicted_limit_crossing_is_rejected(self) -> None:
        decision = SafetySupervisor(limits()).evaluate(
            proposal(
                velocities=(0.5, 0.0),
                execution_duration_ns=50_000_000,
                valid_until_ns=NOW + 50_000_000,
            ),
            body(joint_positions=(1.99, 0.0)),
            health(),
            NOW,
        )
        self.assertEqual(SafetyAction.REJECT, decision.action)
        self.assertEqual("predicted_joint_position_limit", decision.reason)

    def test_calibration_mismatch_stops(self) -> None:
        mismatched_header = ContractHeader(NOW, "planner", "wrong-cal", 1)
        decision = SafetySupervisor(limits()).evaluate(
            proposal(header=mismatched_header), body(), health(), NOW
        )
        self.assertEqual(SafetyAction.STOP, decision.action)
        self.assertEqual("proposal_calibration_mismatch", decision.reason)

    def test_unauthorized_motion_source_is_rejected(self) -> None:
        unauthorized = ContractHeader(NOW, "unknown-planner", CALIBRATION, 1)
        decision = SafetySupervisor(limits()).evaluate(
            proposal(header=unauthorized), body(), health(), NOW
        )
        self.assertEqual(SafetyAction.REJECT, decision.action)
        self.assertEqual("unauthorized_motion_source", decision.reason)


if __name__ == "__main__":
    unittest.main()
