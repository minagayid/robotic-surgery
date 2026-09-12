"""Selective extremity-brain movement orchestration for simulation.

Each extremity owns disjoint joints and validates its own proposal. The
orchestrator wakes only the requested processors; inactive joints are carried
forward unchanged. This is a reference coordination contract, not a motor
driver or a hard real-time safety controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


EXTREMITY_NAMES = ("left_arm", "right_arm", "left_leg", "right_leg")


def _vector(values: Iterable[float], name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result or any(value != value or abs(value) == float("inf") for value in result):
        raise ValueError(f"{name} must contain finite values")
    return result


@dataclass(frozen=True)
class ExtremityCommand:
    processor_id: str
    sequence: int
    created_at_ns: int
    expires_at_ns: int
    target_positions: tuple[float, ...]
    velocities: tuple[float, ...]
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.processor_id not in EXTREMITY_NAMES:
            raise ValueError("unsupported extremity processor")
        if self.sequence < 1 or self.created_at_ns < 0 or self.expires_at_ns <= self.created_at_ns:
            raise ValueError("invalid extremity command sequence or timestamps")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        positions = _vector(self.target_positions, "target_positions")
        velocities = _vector(self.velocities, "velocities")
        if len(positions) != len(velocities):
            raise ValueError("command vectors must have equal dimensions")
        object.__setattr__(self, "target_positions", positions)
        object.__setattr__(self, "velocities", velocities)
        object.__setattr__(self, "confidence", float(self.confidence))


@dataclass(frozen=True)
class ExtremityDecision:
    processor_id: str
    status: str
    reasons: tuple[str, ...]
    effective_velocities: tuple[float, ...]


@dataclass(frozen=True)
class MovementDecision:
    status: str
    active_extremities: tuple[str, ...]
    processor_decisions: tuple[ExtremityDecision, ...]
    effective_joint_positions: tuple[float, ...]
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "active_extremities": list(self.active_extremities),
            "processor_decisions": [item.__dict__ for item in self.processor_decisions],
            "effective_joint_positions": list(self.effective_joint_positions),
            "reasons": list(self.reasons),
            "simulation_only": True,
        }


class ExtremityBrain:
    """Independent local proposal gate for one disjoint extremity."""

    def __init__(
        self,
        processor_id: str,
        joint_indices: tuple[int, ...],
        position_limits: tuple[tuple[float, float], ...],
        max_velocities: tuple[float, ...],
    ) -> None:
        if processor_id not in EXTREMITY_NAMES:
            raise ValueError("unsupported extremity processor")
        if not joint_indices or len(set(joint_indices)) != len(joint_indices):
            raise ValueError("joint_indices must be non-empty and unique")
        if any(index < 0 for index in joint_indices):
            raise ValueError("joint_indices must be non-negative")
        if len(joint_indices) != len(position_limits) or len(joint_indices) != len(max_velocities):
            raise ValueError("brain limits must match joint_indices")
        if any(low >= high for low, high in position_limits) or any(value <= 0 for value in max_velocities):
            raise ValueError("brain limits are invalid")
        self.processor_id = processor_id
        self.joint_indices = tuple(joint_indices)
        self.position_limits = tuple(position_limits)
        self.max_velocities = tuple(float(value) for value in max_velocities)
        self._last_sequence = 0

    def validate(
        self,
        command: ExtremityCommand,
        joint_positions: tuple[float, ...],
        *,
        now_ns: int,
    ) -> ExtremityDecision:
        reasons: list[str] = []
        if command.processor_id != self.processor_id:
            reasons.append("processor_mismatch")
        if any(index >= len(joint_positions) for index in self.joint_indices):
            reasons.append("joint_index_out_of_state")
        if len(command.target_positions) != len(self.joint_indices):
            reasons.append("joint_dimension_mismatch")
        if now_ns < command.created_at_ns:
            reasons.append("future_command")
        if now_ns >= command.expires_at_ns:
            reasons.append("expired_command")
        if command.sequence <= self._last_sequence:
            reasons.append("replayed_sequence")
        if command.confidence < 0.75:
            reasons.append("low_command_confidence")
        if not reasons:
            for offset, (target, bounds, velocity, limit) in enumerate(
                zip(command.target_positions, self.position_limits, command.velocities, self.max_velocities)
            ):
                if not bounds[0] <= target <= bounds[1]:
                    reasons.append(f"joint_{offset}_position_limit")
                if abs(velocity) > limit:
                    reasons.append(f"joint_{offset}_velocity_limit")
        status = "approved" if not reasons else "rejected"
        return ExtremityDecision(self.processor_id, status, tuple(reasons), command.velocities if not reasons else (0.0,) * len(command.velocities))

    def commit(self, command: ExtremityCommand, decision: ExtremityDecision) -> None:
        if decision.status != "approved" or decision.processor_id != self.processor_id:
            raise ValueError("only an approved local decision can commit")
        self._last_sequence = command.sequence


class MovementOrchestrator:
    """Atomically coordinate the requested subset of extremity brains."""

    def __init__(self, brains: Mapping[str, ExtremityBrain]) -> None:
        if set(brains) != set(EXTREMITY_NAMES):
            raise ValueError("exactly four extremity brains are required")
        all_indices = [index for brain in brains.values() for index in brain.joint_indices]
        if len(all_indices) != len(set(all_indices)):
            raise ValueError("extremity brains must own disjoint joints")
        self.brains = dict(brains)

    def orchestrate(
        self,
        commands: Mapping[str, ExtremityCommand],
        joint_positions: tuple[float, ...],
        *,
        now_ns: int,
        active_extremities: tuple[str, ...] | None = None,
    ) -> MovementDecision:
        if not joint_positions:
            raise ValueError("joint_positions must not be empty")
        if active_extremities is None:
            active = EXTREMITY_NAMES
        else:
            requested = tuple(active_extremities)
            if not requested or len(set(requested)) != len(requested) or any(item not in EXTREMITY_NAMES for item in requested):
                return MovementDecision("rejected", (), (), tuple(joint_positions), ("invalid_active_subset",))
            active = tuple(item for item in EXTREMITY_NAMES if item in requested)
        keys = set(commands)
        if keys != set(active):
            reasons = [*(f"missing_command:{item}" for item in active if item not in keys),
                       *(f"inactive_or_unexpected_command:{item}" for item in keys - set(active))]
            return MovementDecision("rejected", active, (), tuple(joint_positions), tuple(reasons))

        decisions = tuple(self.brains[item].validate(commands[item], joint_positions, now_ns=now_ns) for item in active)
        failures = tuple(f"{item.processor_id}:{reason}" for item in decisions if item.status != "approved" for reason in item.reasons)
        if failures:
            return MovementDecision("rejected", active, decisions, tuple(joint_positions), failures)

        effective = list(joint_positions)
        for item in active:
            brain = self.brains[item]
            for index, target in zip(brain.joint_indices, commands[item].target_positions):
                effective[index] = target
        for item in active:
            self.brains[item].commit(commands[item], next(decision for decision in decisions if decision.processor_id == item))
        return MovementDecision("approved", active, decisions, tuple(effective))


def demo_selective_movement(now_ns: int = 100) -> MovementDecision:
    """Run a right-arm-only reference transaction for offline demos."""
    brains = {
        name: ExtremityBrain(
            name,
            (offset * 2, offset * 2 + 1),
            ((-1.0, 1.0), (-1.0, 1.0)),
            (1.0, 1.0),
        )
        for offset, name in enumerate(EXTREMITY_NAMES)
    }
    command = ExtremityCommand(
        "right_arm", sequence=1, created_at_ns=0, expires_at_ns=1_000,
        target_positions=(0.1, -0.1), velocities=(0.5, 0.5),
    )
    return MovementOrchestrator(brains).orchestrate(
        {"right_arm": command}, (0.0,) * 8, now_ns=now_ns,
        active_extremities=("right_arm",),
    )
