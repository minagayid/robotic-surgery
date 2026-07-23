"""Offline simulated safe-motion demonstration."""

from __future__ import annotations

from pathlib import Path
import tempfile

from .actuator import SimulatedVelocityActuator
from .clock import ManualClock
from .contracts import BodyState, ContractHeader, HealthSnapshot, MotionProposal, SafetyLimits
from .events import EventJournal
from .runtime import RobotRuntime
from .safety import SafetySupervisor


def main() -> None:
    clock = ManualClock(1_000_000_000)
    calibration_id = "demo-arm-cal-v1"
    limits = SafetyLimits(
        calibration_id=calibration_id,
        authorized_motion_sources=("demo",),
        authorized_state_sources=("demo",),
        joint_position_min=(-3.14, -2.0),
        joint_position_max=(3.14, 2.0),
        max_joint_velocity=(0.5, 0.4),
        max_joint_effort=(20.0, 15.0),
    )
    log_path = Path(tempfile.gettempdir()) / "robotx-os" / "demo-events.jsonl"
    log_path.unlink(missing_ok=True)
    runtime = RobotRuntime(
        clock=clock,
        supervisor=SafetySupervisor(limits),
        actuator=SimulatedVelocityActuator(),
        journal=EventJournal(log_path),
    )
    header = ContractHeader(clock.now_ns(), "demo", calibration_id, sequence=1)
    state = BodyState(header, (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), 1.0, True)
    health = HealthSnapshot(clock.now_ns(), hardware_safety_ready=True, configuration_verified=True)
    proposal = MotionProposal(
        header, "demo-1", clock.now_ns() + 20_000_000, (0.8, 0.1), 10_000_000
    )
    decision, next_state = runtime.execute(proposal, state, health)
    print(f"decision={decision.action.value} reason={decision.reason}")
    print(f"approved_velocities={decision.approved_joint_velocities}")
    print(f"next_positions={next_state.joint_positions}")
    print(f"verified_event_log={log_path}")


if __name__ == "__main__":
    main()
