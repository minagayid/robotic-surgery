"""A concrete, simulation-only workcell profile for repeatable validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkcellProfile:
    profile_id: str
    revision: str
    mode: str
    simulator: str
    middleware: str
    compute_target: str
    control_loop_hz: int
    state_loop_hz: int
    joint_count: int
    coordinate_frames: tuple[str, ...]
    independent_safety_boundary: str
    actuation_policy: str

    def __post_init__(self) -> None:
        if not self.profile_id or not self.revision:
            raise ValueError("workcell identity is required")
        if self.mode != "simulation_only":
            raise ValueError("the reference profile must remain simulation_only")
        if self.control_loop_hz < 1 or self.state_loop_hz < 1 or self.joint_count < 1:
            raise ValueError("workcell rates and joint count must be positive")
        if not self.coordinate_frames or len(set(self.coordinate_frames)) != len(self.coordinate_frames):
            raise ValueError("workcell coordinate frames must be unique")
        if "no_hardware" not in self.actuation_policy:
            raise ValueError("the reference profile must declare no hardware actuation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "revision": self.revision,
            "mode": self.mode,
            "simulator": self.simulator,
            "middleware": self.middleware,
            "compute_target": self.compute_target,
            "control_loop_hz": self.control_loop_hz,
            "state_loop_hz": self.state_loop_hz,
            "joint_count": self.joint_count,
            "coordinate_frames": list(self.coordinate_frames),
            "independent_safety_boundary": self.independent_safety_boundary,
            "actuation_policy": self.actuation_policy,
        }


DEFAULT_WORKCELL_PROFILE = WorkcellProfile(
    profile_id="robotx-reference-four-extremity-v1",
    revision="2026-09-10",
    mode="simulation_only",
    simulator="deterministic-offline",
    middleware="none-in-reference-runtime",
    compute_target="host-cpu-reference",
    control_loop_hz=1_000,
    state_loop_hz=100,
    joint_count=8,
    coordinate_frames=("base", "workcell", "upper_coordinator", "lower_coordinator", "left_arm", "right_arm", "left_leg", "right_leg"),
    independent_safety_boundary="independent-safety-controller-reference",
    actuation_policy="no_hardware_or_network_access",
)
