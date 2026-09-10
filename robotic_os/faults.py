"""Deterministic fault injection helpers used by safety verification tests."""

from __future__ import annotations

from dataclasses import replace

from .contracts import RobotState


class FaultInjector:
    """Create invalid-but-realistic state evidence without touching hardware."""

    @staticmethod
    def stale_heartbeat(state: RobotState, *, now_ns: int, timeout_ns: int) -> RobotState:
        return replace(state, timestamp_ns=max(0, now_ns - timeout_ns - 1))

    @staticmethod
    def unhealthy_sensor(state: RobotState, index: int = 0) -> RobotState:
        if index < 0 or index >= len(state.sensor_health):
            raise IndexError("sensor index out of range")
        health = list(state.sensor_health)
        health[index] = False
        return replace(state, sensor_health=tuple(health))

    @staticmethod
    def emergency_stop(state: RobotState) -> RobotState:
        return replace(state, emergency_stop=True)
