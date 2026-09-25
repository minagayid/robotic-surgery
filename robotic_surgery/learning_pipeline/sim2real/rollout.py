"""Simulation-only rollout with logging; no hardware adapter is implemented."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import SafetyConfig
from ..learning.vla_policy import VLAPolicy
from ..types import FrameStack, RobotAction, RobotDemonstration
from .safety import SafetyEnvelope, SafetyViolation
from .validation import ValidationReport


@dataclass
class StepLog:
    step: int
    gripper: float
    clamped: bool


@dataclass
class RolloutLog:
    instruction: str
    steps: list[StepLog] = field(default_factory=list)
    success: bool = False
    aborted: bool = False
    abort_reason: str = ""

    def to_demonstration(self, episode_id: str,
                         observations: list[FrameStack],
                         actions: list[RobotAction]) -> RobotDemonstration:
        """Wrap rollout records for API tests; this is not a robot demonstration."""
        return RobotDemonstration(
            episode_id=episode_id,
            observations=observations,
            actions=actions,
            language_instruction=self.instruction,
            success=self.success,
        )


class StagedRollout:
    def __init__(self, safety_cfg: SafetyConfig | None = None,
                 min_sim_success_rate: float = 0.6):
        if not 0.0 <= min_sim_success_rate <= 1.0:
            raise ValueError("min_sim_success_rate must be between 0 and 1")
        self.safety_cfg = safety_cfg or SafetyConfig()
        self.min_sim_success_rate = min_sim_success_rate

    def gate(self, report: ValidationReport) -> None:
        """Require a valid, non-empty toy-simulation report before another sim run."""
        if report.episodes < 1 or not 0 <= report.successes <= report.episodes:
            raise SafetyViolation("simulation validation report has invalid episode counts")
        if report.success_rate < self.min_sim_success_rate:
            raise SafetyViolation(
                f"sim success rate {report.success_rate:.2f} < required "
                f"{self.min_sim_success_rate:.2f}; follow-on simulation blocked"
            )

    def run(self, policy: VLAPolicy, env, instruction: str,
            report: ValidationReport, horizon: int = 20) -> RolloutLog:
        """Run a rollout only against an explicitly marked simulation environment."""
        if getattr(env, "simulation_only", False) is not True:
            raise SafetyViolation("only simulation_only environments are supported")
        initial_position = getattr(env, "ee_position_m", None)
        if initial_position is None:
            raise SafetyViolation("simulation environment must expose measured ee_position_m")
        self.gate(report)
        envelope = SafetyEnvelope(self.safety_cfg, initial_position_m=tuple(initial_position))
        log = RolloutLog(instruction=instruction)
        try:
            envelope.preflight()
            for t in range(horizon):
                obs = env.observe()
                action = policy.act(obs, instruction)
                before = len(envelope.events)
                safe = envelope.clamp(action, step=t)
                clamped = len(envelope.events) > before
                result = env.step(safe)
                done, success = result if isinstance(result, tuple) else (result, result)
                log.steps.append(StepLog(t, round(safe.gripper, 3), clamped))
                if done:
                    log.success = bool(success)
                    break
        except SafetyViolation as e:
            log.aborted = True
            log.abort_reason = str(e)
        return log
