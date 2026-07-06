import numpy as np
import pytest

from robotx.config import SafetyConfig
from robotx.learning.vla_policy import MockVLAPolicy
from robotx.retargeting.representation import MockVisualEncoder
from robotx.sim2real.rollout import StagedRollout
from robotx.sim2real.safety import SafetyEnvelope, SafetyViolation
from robotx.sim2real.validation import SimValidator, ValidationReport, _KinematicSim
from robotx.types import RobotAction


def test_safety_clamps_speed():
    env = SafetyEnvelope(SafetyConfig(max_ee_speed=0.1))
    a0 = RobotAction(ee_pose=np.eye(4), gripper=0.5)
    env.clamp(a0, dt=0.1, step=0)
    far = np.eye(4)
    far[:3, 3] = [10.0, 0, 0]           # absurd jump
    out = env.clamp(RobotAction(ee_pose=far, gripper=0.5), dt=0.1, step=1)
    moved = np.linalg.norm(out.ee_pose[:3, 3])
    assert moved <= 0.1 * 0.1 + 1e-6    # within max_ee_speed * dt
    assert any(e.kind == "speed" for e in env.events)


def test_safety_preflight_refuses_when_kill_engaged():
    env = SafetyEnvelope(SafetyConfig(require_kill_switch=True))
    env.engage_kill_switch()
    with pytest.raises(SafetyViolation):
        env.preflight()


def test_sim_validation_runs():
    enc = MockVisualEncoder()
    policy = MockVLAPolicy(enc)
    report = SimValidator(domain_randomize=True).validate(policy, "pick up cup", episodes=5)
    assert isinstance(report, ValidationReport)
    assert report.episodes == 5
    assert 0.0 <= report.success_rate <= 1.0
    assert len(report.randomizations) == 5


def test_staged_rollout_gates_on_sim_success():
    enc = MockVisualEncoder()
    policy = MockVLAPolicy(enc)
    rollout = StagedRollout(SafetyConfig(staged_rollout=True), min_sim_success_rate=0.9)
    bad = ValidationReport(episodes=10, successes=1, safety_clamps=0)  # 10% success
    with pytest.raises(SafetyViolation):
        rollout.gate(bad)


def test_staged_rollout_runs_when_cleared():
    enc = MockVisualEncoder()
    policy = MockVLAPolicy(enc)
    rollout = StagedRollout(SafetyConfig(), min_sim_success_rate=0.0)
    good = ValidationReport(episodes=10, successes=8, safety_clamps=0)

    sim = _KinematicSim(seed=1, randomize=False)

    class Env:
        def observe(self):
            return sim.observe()

        def step(self, action):
            d = sim.step(action)
            return d, d

    log = rollout.run(policy, Env(), "pick up cup", good, horizon=15)
    assert not log.aborted
    assert len(log.steps) >= 1
