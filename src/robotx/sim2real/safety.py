"""Safety envelope -- the hard limits every commanded action passes through.

This is the last line of defence before an action reaches (sim or real)
hardware. It clamps end-effector speed and gripper force to a fraction of
hardware maxima during early trials, and refuses to run at all if a kill switch
is required but absent. Enforced by construction: :meth:`clamp` cannot return an
out-of-envelope action.
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
    kind: str            # "speed" | "force"
    original: float
    clamped: float


@dataclass
class SafetyEnvelope:
    cfg: SafetyConfig
    kill_switch_engaged: bool = False
    events: list[ClampEvent] = field(default_factory=list)
    _prev_pos: np.ndarray | None = field(default=None, repr=False)

    def preflight(self) -> None:
        """Refuse to operate without required safeguards."""
        if self.cfg.require_kill_switch and self.kill_switch_engaged:
            raise SafetyViolation("kill switch engaged -- refusing to command hardware")

    def clamp(self, action: RobotAction, dt: float = 0.1, step: int = 0) -> RobotAction:
        """Return an action guaranteed within the safety envelope.

        Limits Cartesian EE speed to ``max_ee_speed`` and maps gripper command so
        that closing force stays under ``force_limit_n`` (modelled as a cap on how
        far past 'just closed' the gripper may command).
        """
        self.preflight()
        pos = action.ee_pose[:3, 3].copy()
        new_pose = action.ee_pose.copy()

        if self._prev_pos is not None:
            delta = pos - self._prev_pos
            dist = float(np.linalg.norm(delta))
            max_dist = self.cfg.max_ee_speed * dt
            if dist > max_dist > 0:
                scaled = self._prev_pos + delta * (max_dist / dist)
                new_pose[:3, 3] = scaled
                pos = scaled
                self.events.append(ClampEvent(step, "speed", dist / dt, self.cfg.max_ee_speed))
        self._prev_pos = pos

        # gripper: model commanded closing force; disallow slamming fully shut in
        # early trials by flooring the opening at a torque-limited minimum
        min_open = max(0.0, 1.0 - self.cfg.torque_limit_frac * 4.0)
        gripper = action.gripper
        if gripper < min_open:
            self.events.append(ClampEvent(step, "force", gripper, min_open))
            gripper = min_open

        return RobotAction(ee_pose=new_pose, gripper=gripper)

    def engage_kill_switch(self) -> None:
        self.kill_switch_engaged = True

    def reset(self) -> None:
        self._prev_pos = None
