"""Versioned, immutable contracts crossing RobotX runtime boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import math
from typing import Any


SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class ContractHeader:
    monotonic_ns: int
    source_id: str
    calibration_id: str
    sequence: int
    confidence: float = 1.0
    schema_version: int = SCHEMA_VERSION

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.schema_version != SCHEMA_VERSION:
            errors.append("unsupported_schema")
        if self.monotonic_ns < 0:
            errors.append("negative_timestamp")
        if not self.source_id:
            errors.append("missing_source")
        if not self.calibration_id:
            errors.append("missing_calibration")
        if self.sequence < 0:
            errors.append("negative_sequence")
        if not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            errors.append("invalid_confidence")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class BodyState:
    header: ContractHeader
    joint_positions: tuple[float, ...]
    joint_velocities: tuple[float, ...]
    joint_efforts: tuple[float, ...]
    nearest_obstacle_m: float
    actuator_power_enabled: bool

    def is_finite(self) -> bool:
        values = (
            *self.joint_positions,
            *self.joint_velocities,
            *self.joint_efforts,
            self.nearest_obstacle_m,
        )
        return all(math.isfinite(value) for value in values)


@dataclass(frozen=True, slots=True)
class MotionProposal:
    header: ContractHeader
    proposal_id: str
    valid_until_ns: int
    target_joint_velocities: tuple[float, ...]
    execution_duration_ns: int
    expected_contact: bool = False

    def is_finite(self) -> bool:
        return all(math.isfinite(value) for value in self.target_joint_velocities)


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    heartbeat_ns: int
    physical_estop_engaged: bool = False
    hardware_safety_ready: bool = False
    configuration_verified: bool = False


@dataclass(frozen=True, slots=True)
class SafetyLimits:
    calibration_id: str
    authorized_motion_sources: tuple[str, ...]
    authorized_state_sources: tuple[str, ...]
    joint_position_min: tuple[float, ...]
    joint_position_max: tuple[float, ...]
    max_joint_velocity: tuple[float, ...]
    max_joint_effort: tuple[float, ...]
    heartbeat_timeout_ns: int = 100_000_000
    state_timeout_ns: int = 50_000_000
    max_command_duration_ns: int = 50_000_000
    future_tolerance_ns: int = 2_000_000
    minimum_obstacle_distance_m: float = 0.15
    reset_velocity_tolerance: float = 0.01
    minimum_confidence: float = 0.8

    def __post_init__(self) -> None:
        joint_count = len(self.joint_position_min)
        dimensions = (
            len(self.joint_position_max),
            len(self.max_joint_velocity),
            len(self.max_joint_effort),
        )
        if joint_count == 0 or any(size != joint_count for size in dimensions):
            raise ValueError("all safety-limit vectors must have the same non-zero size")
        if not self.calibration_id:
            raise ValueError("calibration_id is required")
        if not self.authorized_motion_sources or not self.authorized_state_sources:
            raise ValueError("authorized source allowlists cannot be empty")
        if any(not source for source in (*self.authorized_motion_sources, *self.authorized_state_sources)):
            raise ValueError("authorized source identifiers cannot be empty")
        if len(set(self.authorized_motion_sources)) != len(self.authorized_motion_sources):
            raise ValueError("motion source identifiers must be unique")
        if len(set(self.authorized_state_sources)) != len(self.authorized_state_sources):
            raise ValueError("state source identifiers must be unique")
        if any(low >= high for low, high in zip(self.joint_position_min, self.joint_position_max)):
            raise ValueError("each joint minimum must be below its maximum")
        if any(limit <= 0.0 or not math.isfinite(limit) for limit in self.max_joint_velocity):
            raise ValueError("velocity limits must be finite and positive")
        if any(limit <= 0.0 or not math.isfinite(limit) for limit in self.max_joint_effort):
            raise ValueError("effort limits must be finite and positive")
        if (
            self.heartbeat_timeout_ns <= 0
            or self.state_timeout_ns <= 0
            or self.max_command_duration_ns <= 0
        ):
            raise ValueError("timeouts must be positive")
        if self.future_tolerance_ns < 0:
            raise ValueError("future tolerance cannot be negative")
        if self.minimum_obstacle_distance_m < 0.0:
            raise ValueError("minimum obstacle distance cannot be negative")
        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError("minimum confidence must be in [0, 1]")

    @property
    def joint_count(self) -> int:
        return len(self.joint_position_min)


class SafetyAction(str, Enum):
    APPROVE = "approve"
    CLAMP = "clamp"
    REJECT = "reject"
    STOP = "stop"


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    action: SafetyAction
    reason: str
    proposal_id: str
    decided_at_ns: int
    approved_joint_velocities: tuple[float, ...] = ()
    approved_duration_ns: int = 0
    stop_latched: bool = False


def contract_to_dict(value: Any) -> dict[str, Any]:
    """Convert a contract to stable JSON-compatible primitives."""
    result = asdict(value)
    for key, item in tuple(result.items()):
        if isinstance(item, Enum):
            result[key] = item.value
    return result
