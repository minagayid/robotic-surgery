"""Staged real-world rollout with logging (Section 5).

Gated behind a passing :class:`~robotx.sim2real.validation.ValidationReport`:
a policy that has not cleared a success-rate bar in sim is not allowed onto
hardware. Runs under the :class:`~robotx.sim2real.safety.SafetyEnvelope`, logs
every step, and emits success/failure episodes that feed back into the ops loop
-- because real robot experience is higher-value than more human video.
"""

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
        """Convert a completed rollout into a (high-value) robot demonstration."""
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
        self.safety_cfg = safety_cfg or SafetyConfig()
        self.min_sim_success_rate = min_sim_success_rate

    def gate(self, report: ValidationReport) -> None:
        """Refuse hardware rollout unless sim validation cleared the bar."""
        if self.safety_cfg.staged_rollout and report.success_rate < self.min_sim_success_rate:
            raise SafetyViolation(
                f"sim success rate {report.success_rate:.2f} < required "
                f"{self.min_sim_success_rate:.2f} -- not cleared for hardware"
            )

    def run(self, policy: VLAPolicy, env, instruction: str,
            report: ValidationReport, horizon: int = 20) -> RolloutLog:
        """Run one supervised rollout on ``env`` (must expose observe/step).

        ``env.step(action)`` returns (done, success). A real deployment passes a
        hardware driver here; tests pass a sim.
        """
        self.gate(report)
        envelope = SafetyEnvelope(self.safety_cfg)
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
