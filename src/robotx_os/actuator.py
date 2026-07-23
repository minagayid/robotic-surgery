"""Actuator boundary interfaces and a deterministic simulation adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contracts import BodyState, SafetyAction, SafetyDecision


class ActuatorBoundary(Protocol):
    def apply(self, decision: SafetyDecision, state: BodyState) -> BodyState: ...


@dataclass(slots=True)
class SimulatedVelocityActuator:
    """Simple bounded integrator for tests; never use as a hardware driver."""

    def apply(self, decision: SafetyDecision, state: BodyState) -> BodyState:
        can_move = decision.action in (SafetyAction.APPROVE, SafetyAction.CLAMP)
        velocities = decision.approved_joint_velocities if can_move else (0.0,) * len(state.joint_positions)
        seconds = decision.approved_duration_ns / 1_000_000_000
        positions = tuple(
            position + velocity * seconds
            for position, velocity in zip(state.joint_positions, velocities)
        )
        return BodyState(
            header=state.header,
            joint_positions=positions,
            joint_velocities=velocities,
            joint_efforts=state.joint_efforts,
            nearest_obstacle_m=state.nearest_obstacle_m,
            actuator_power_enabled=can_move and not decision.stop_latched,
        )
