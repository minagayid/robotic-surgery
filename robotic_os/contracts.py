"""Versioned, JSON-friendly contracts for the reference runtime."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable


SCHEMA_VERSION = 1


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _numbers(values: Iterable[float], name: str) -> tuple[float, ...]:
    try:
        result = tuple(_finite(value, name) for value in values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence") from exc
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


@dataclass(frozen=True)
class MotionProposal:
    source_id: str
    sequence: int
    calibration_id: str
    created_at_ns: int
    expires_at_ns: int
    duration_ms: int
    target_positions: tuple[float, ...]
    velocities: tuple[float, ...]
    force_limits_n: tuple[float, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.source_id or len(self.source_id) > 120:
            raise ValueError("source_id must be a non-empty short identifier")
        if not self.calibration_id or len(self.calibration_id) > 120:
            raise ValueError("calibration_id must be a non-empty short identifier")
        if self.sequence < 1:
            raise ValueError("sequence must be positive")
        if self.created_at_ns < 0 or self.expires_at_ns <= self.created_at_ns:
            raise ValueError("proposal timestamps are invalid")
        if self.duration_ms < 1:
            raise ValueError("duration_ms must be positive")
        positions = _numbers(self.target_positions, "target_positions")
        velocities = _numbers(self.velocities, "velocities")
        forces = _numbers(self.force_limits_n, "force_limits_n")
        if len(positions) != len(velocities) or len(positions) != len(forces):
            raise ValueError("motion vectors must have equal dimensions")
        if any(force < 0 for force in forces):
            raise ValueError("force_limits_n must not be negative")
        object.__setattr__(self, "target_positions", positions)
        object.__setattr__(self, "velocities", velocities)
        object.__setattr__(self, "force_limits_n", forces)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "sequence": self.sequence,
            "calibration_id": self.calibration_id,
            "created_at_ns": self.created_at_ns,
            "expires_at_ns": self.expires_at_ns,
            "duration_ms": self.duration_ms,
            "target_positions": list(self.target_positions),
            "velocities": list(self.velocities),
            "force_limits_n": list(self.force_limits_n),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MotionProposal":
        if int(data.get("schema_version", SCHEMA_VERSION)) != SCHEMA_VERSION:
            raise ValueError("unsupported motion proposal schema")
        return cls(
            source_id=str(data["source_id"]),
            sequence=int(data["sequence"]),
            calibration_id=str(data["calibration_id"]),
            created_at_ns=int(data["created_at_ns"]),
            expires_at_ns=int(data["expires_at_ns"]),
            duration_ms=int(data["duration_ms"]),
            target_positions=tuple(data["target_positions"]),
            velocities=tuple(data["velocities"]),
            force_limits_n=tuple(data["force_limits_n"]),
            schema_version=SCHEMA_VERSION,
        )


@dataclass(frozen=True)
class RobotState:
    timestamp_ns: int
    calibration_id: str
    joint_positions: tuple[float, ...]
    heartbeat_seq: int
    proximity_m: float
    sensor_health: tuple[bool, ...]
    emergency_stop: bool = False

    def __post_init__(self) -> None:
        if self.timestamp_ns < 0:
            raise ValueError("timestamp_ns must be non-negative")
        if not self.calibration_id:
            raise ValueError("calibration_id must not be empty")
        if self.heartbeat_seq < 0:
            raise ValueError("heartbeat_seq must not be negative")
        positions = _numbers(self.joint_positions, "joint_positions")
        health = tuple(bool(value) for value in self.sensor_health)
        if len(positions) != len(health):
            raise ValueError("joint_positions and sensor_health must match")
        proximity = _finite(self.proximity_m, "proximity_m")
        if proximity < 0:
            raise ValueError("proximity_m must not be negative")
        object.__setattr__(self, "joint_positions", positions)
        object.__setattr__(self, "sensor_health", health)
        object.__setattr__(self, "proximity_m", proximity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_ns": self.timestamp_ns,
            "calibration_id": self.calibration_id,
            "joint_positions": list(self.joint_positions),
            "heartbeat_seq": self.heartbeat_seq,
            "proximity_m": self.proximity_m,
            "sensor_health": list(self.sensor_health),
            "emergency_stop": self.emergency_stop,
        }


@dataclass(frozen=True)
class SafetyLimits:
    position_limits: tuple[tuple[float, float], ...]
    max_velocity: tuple[float, ...]
    max_force_n: tuple[float, ...]
    min_proximity_m: float
    max_command_duration_ms: int

    def __post_init__(self) -> None:
        position_limits = tuple((float(low), float(high)) for low, high in self.position_limits)
        velocities = _numbers(self.max_velocity, "max_velocity")
        forces = _numbers(self.max_force_n, "max_force_n")
        if len(position_limits) != len(velocities) or len(position_limits) != len(forces):
            raise ValueError("safety limit dimensions must match")
        for low, high in position_limits:
            if not math.isfinite(low) or not math.isfinite(high) or low >= high:
                raise ValueError("position limits must be finite low/high pairs")
        if any(value <= 0 for value in velocities) or any(value <= 0 for value in forces):
            raise ValueError("velocity and force limits must be positive")
        proximity = _finite(self.min_proximity_m, "min_proximity_m")
        if proximity < 0 or self.max_command_duration_ms < 1:
            raise ValueError("safety limits contain invalid bounds")
        object.__setattr__(self, "position_limits", position_limits)
        object.__setattr__(self, "max_velocity", velocities)
        object.__setattr__(self, "max_force_n", forces)
        object.__setattr__(self, "min_proximity_m", proximity)


@dataclass(frozen=True)
class SafetyDecision:
    status: str
    reasons: tuple[str, ...]
    source_id: str
    sequence: int
    timestamp_ns: int
    effective_velocities: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "source_id": self.source_id,
            "sequence": self.sequence,
            "timestamp_ns": self.timestamp_ns,
            "effective_velocities": list(self.effective_velocities),
        }
