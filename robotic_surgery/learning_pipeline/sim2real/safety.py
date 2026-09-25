"""Toy-simulation command bounds.

This code has no actuator connection and no physical force or torque feedback.
It limits simulated Cartesian step distance and normalized gripper closure only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import SafetyConfig
from ..types import RobotAction


class SafetyViolation(RuntimeError):
    pass


@dataclass
class ClampEvent:
    step: int
    kind: str            # "speed" | "gripper_closure"
    original: float
    clamped: float


@dataclass
class SafetyEnvelope:
    cfg: SafetyConfig
    initial_position_m: tuple[float, float, float] | None = None
    kill_switch_engaged: bool = False
    events: list[ClampEvent] = field(default_factory=list)
    _prev_pos: np.ndarray | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.initial_position_m is not None:
            position = np.asarray(self.initial_position_m, dtype=float)
            if position.shape != (3,) or not np.isfinite(position).all():
                raise ValueError("initial_position_m must be a finite 3-vector")
            self._prev_pos = position.copy()

    def preflight(self) -> None:
        """Reject when the simulated stop latch is engaged."""
        if self.kill_switch_engaged:
            raise SafetyViolation("simulated stop latch engaged")

    def clamp(self, action: RobotAction, dt: float = 0.1, step: int = 0) -> RobotAction:
        """Clamp a simulated pose step and normalized gripper closure command."""
        self.preflight()
        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        if step < 0:
            raise ValueError("step must be non-negative")
        pos = action.ee_pose[:3, 3].copy()
        if pos.shape != (3,) or not np.isfinite(pos).all():
            raise SafetyViolation("simulated target position must be a finite 3-vector")
        new_pose = action.ee_pose.copy()

        if self._prev_pos is None:
            raise SafetyViolation("a measured initial end-effector position is required")
        delta = pos - self._prev_pos
        dist = float(np.linalg.norm(delta))
        max_dist = self.cfg.max_ee_speed_m_s * dt
        if dist > max_dist:
            scaled = self._prev_pos + delta * (max_dist / dist)
            new_pose[:3, 3] = scaled
            pos = scaled
            self.events.append(ClampEvent(step, "speed", dist / dt, self.cfg.max_ee_speed_m_s))
        self._prev_pos = pos

        # RobotAction.gripper is normalized: 0 is closed, 1 is open. This is a
        # travel-command cap only; force cannot be inferred from this scalar.
        min_open = 1.0 - self.cfg.max_gripper_closure_fraction
        gripper = action.gripper
        if gripper < min_open:
            self.events.append(ClampEvent(step, "gripper_closure", gripper, min_open))
            gripper = min_open

        return RobotAction(ee_pose=new_pose, gripper=gripper)

    def engage_kill_switch(self) -> None:
        self.kill_switch_engaged = True

    def reset(self, measured_position_m: tuple[float, float, float]) -> None:
        position = np.asarray(measured_position_m, dtype=float)
        if position.shape != (3,) or not np.isfinite(position).all():
            raise ValueError("measured_position_m must be a finite 3-vector")
        self._prev_pos = position.copy()
        self.kill_switch_engaged = False
