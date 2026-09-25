import numpy as np
import pytest

from robotic_surgery.learning_pipeline.config import SafetyConfig
from robotic_surgery.learning_pipeline.learning.vla_policy import MockVLAPolicy
from robotic_surgery.learning_pipeline.retargeting.representation import MockVisualEncoder
from robotic_surgery.learning_pipeline.sim2real.rollout import StagedRollout
from robotic_surgery.learning_pipeline.sim2real.safety import SafetyEnvelope, SafetyViolation
from robotic_surgery.learning_pipeline.sim2real.validation import SimValidator, ValidationReport, _KinematicSim
from robotic_surgery.learning_pipeline.types import RobotAction


def test_safety_clamps_speed():
    env = SafetyEnvelope(SafetyConfig(max_ee_speed_m_s=0.1), initial_position_m=(0.0, 0.0, 0.0))
    a0 = RobotAction(ee_pose=np.eye(4), gripper=0.5)
    env.clamp(a0, dt=0.1, step=0)
    far = np.eye(4)
    far[:3, 3] = [10.0, 0, 0]           # absurd jump
    out = env.clamp(RobotAction(ee_pose=far, gripper=0.5), dt=0.1, step=1)
    moved = np.linalg.norm(out.ee_pose[:3, 3])
    assert moved <= 0.1 * 0.1 + 1e-6    # within max_ee_speed * dt
    assert any(e.kind == "speed" for e in env.events)


def test_safety_preflight_refuses_when_kill_engaged():
    env = SafetyEnvelope(SafetyConfig())
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
    rollout = StagedRollout(SafetyConfig(), min_sim_success_rate=0.9)
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
        simulation_only = True

        @property
        def ee_position_m(self):
            return tuple(sim.ee)

        def observe(self):
            return sim.observe()

        def step(self, action):
            d = sim.step(action)
            return d, d

    log = rollout.run(policy, Env(), "pick up cup", good, horizon=15)
    assert not log.aborted
    assert len(log.steps) >= 1


def test_staged_rollout_rejects_unmarked_environment():
    rollout = StagedRollout(SafetyConfig(), min_sim_success_rate=0.0)
    good = ValidationReport(episodes=10, successes=8, safety_clamps=0)

    class UnknownEnvironment:
        def observe(self):
            raise AssertionError("environment must be rejected before observation")

        def step(self, action):
            raise AssertionError("environment must be rejected before command")

    with pytest.raises(SafetyViolation, match="simulation_only"):
        rollout.run(MockVLAPolicy(MockVisualEncoder()), UnknownEnvironment(), "test", good)


def test_speed_limiter_requires_measured_initial_position():
    env = SafetyEnvelope(SafetyConfig())
    with pytest.raises(SafetyViolation, match="initial end-effector position"):
        env.clamp(RobotAction(ee_pose=np.eye(4), gripper=0.5))
