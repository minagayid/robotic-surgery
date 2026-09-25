"""Toy randomized kinematic simulation for offline plumbing checks.

The environment is not a stand-in for validated MuJoCo/Isaac physics: it moves
an end-effector point toward a goal and synthesizes image brightness from
distance. The reported success rate and clamps are not evidence of robot
performance or safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import SafetyConfig
from ..learning.vla_policy import VLAPolicy
from ..types import FrameStack, RobotAction
from .safety import SafetyEnvelope


@dataclass
class ValidationReport:
    episodes: int
    successes: int
    safety_clamps: int
    randomizations: list[dict] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.successes / self.episodes if self.episodes else 0.0


class _KinematicSim:
    """Minimal goal-reaching sim: EE must get near a randomized target.

    Observations are synthetic frames whose brightness encodes the remaining
    distance to goal, so a retrieval/goal-conditioned policy has signal.
    """

    def __init__(self, seed: int, randomize: bool):
        self.rng = np.random.default_rng(seed)
        self.randomize = randomize
        self.goal = self.rng.uniform(-0.2, 0.2, size=3)
        self.ee = np.zeros(3)
        self.friction = float(self.rng.uniform(0.8, 1.2)) if randomize else 1.0
        self.lighting = float(self.rng.uniform(0.7, 1.3)) if randomize else 1.0

    def observe(self) -> FrameStack:
        dist = np.linalg.norm(self.goal - self.ee)
        val = np.clip(255 * (1 - dist) * self.lighting, 0, 255)
        frame = np.full((8, 8, 3), int(val), dtype=np.uint8)
        return FrameStack(frames=frame[None], frame_indices=[0], sample_fps=1.0)

    def step(self, action: RobotAction, dt: float = 0.1) -> bool:
        target = action.ee_pose[:3, 3]
        # move toward commanded pose, scaled by (randomized) friction
        self.ee = self.ee + (target - self.ee) * 0.5 / self.friction
        return bool(np.linalg.norm(self.goal - self.ee) < 0.05)

    def config(self) -> dict:
        return {"friction": round(self.friction, 3), "lighting": round(self.lighting, 3),
                "goal": [round(g, 3) for g in self.goal]}


class SimValidator:
    def __init__(self, safety_cfg: SafetyConfig | None = None, domain_randomize: bool = True):
        self.safety_cfg = safety_cfg or SafetyConfig()
        self.domain_randomize = domain_randomize

    def validate(self, policy: VLAPolicy, instruction: str,
                 episodes: int = 10, horizon: int = 20, seed: int = 0) -> ValidationReport:
        successes = 0
        total_clamps = 0
        randomizations = []
        for ep in range(episodes):
            sim = _KinematicSim(seed + ep, self.domain_randomize)
            envelope = SafetyEnvelope(self.safety_cfg, initial_position_m=tuple(sim.ee))
            done = False
            for t in range(horizon):
                obs = sim.observe()
                action = policy.act(obs, instruction)
                safe = envelope.clamp(action, step=t)
                done = sim.step(safe)
                if done:
                    break
            successes += int(done)
            total_clamps += len(envelope.events)
            randomizations.append(sim.config())
        return ValidationReport(episodes, successes, total_clamps, randomizations)
