"""Fail-closed actuation contracts for simulation and future ROS2 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .contracts import MotionProposal


class AdapterUnavailable(RuntimeError):
    """Raised when an external actuator path is not explicitly enabled."""


@dataclass(frozen=True)
class ActuationReceipt:
    accepted: bool
    adapter_id: str
    timestamp_ns: int
    external_action: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "adapter_id": self.adapter_id,
            "timestamp_ns": self.timestamp_ns,
            "external_action": self.external_action,
            "reasons": list(self.reasons),
        }


class ActuatorAdapter(Protocol):
    adapter_id: str

    def apply(self, proposal: MotionProposal, *, now_ns: int) -> ActuationReceipt:
        ...


class SimulationActuatorAdapter:
    """Records a command as a simulation event and performs no external action."""

    adapter_id = "robotx.simulation-actuator"

    def apply(self, proposal: MotionProposal, *, now_ns: int) -> ActuationReceipt:
        return ActuationReceipt(
            accepted=True,
            adapter_id=self.adapter_id,
            timestamp_ns=now_ns,
            external_action=False,
        )


class ROS2AdapterContract:
    """Message-shape contract; it deliberately has no ROS2 dependency or socket."""

    adapter_id = "robotx.ros2-contract"

    def __init__(self, topic_map: dict[str, str] | None = None) -> None:
        self.topic_map = dict(topic_map or {})
        self.connected = False

    def build_message(self, proposal: MotionProposal) -> dict[str, Any]:
        return {
            "schema_version": proposal.schema_version,
            "source_id": proposal.source_id,
            "sequence": proposal.sequence,
            "calibration_id": proposal.calibration_id,
            "target_positions": list(proposal.target_positions),
            "velocities": list(proposal.velocities),
            "force_limits_n": list(proposal.force_limits_n),
            "topics": dict(self.topic_map),
        }

    def apply(self, proposal: MotionProposal, *, now_ns: int) -> ActuationReceipt:
        if not self.connected:
            raise AdapterUnavailable("ROS2 adapter contract is disconnected")
        raise AdapterUnavailable("ROS2 runtime binding is not included in the reference package")


class HardwareAbstractionLayer:
    """Single injection point that keeps runtime actuation fail-closed."""

    def __init__(self, adapter: ActuatorAdapter | None = None) -> None:
        self.adapter = adapter or SimulationActuatorAdapter()

    @property
    def adapter_id(self) -> str:
        return self.adapter.adapter_id

    def apply(self, proposal: MotionProposal, *, now_ns: int) -> ActuationReceipt:
        return self.adapter.apply(proposal, now_ns=now_ns)
