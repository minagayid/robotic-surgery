import numpy as np

from robotic_surgery.learning_pipeline.learning.planner import HighLevelPlanner
from robotic_surgery.learning_pipeline.learning.pretrain import RepresentationTrainer
from robotic_surgery.learning_pipeline.learning.vla_policy import MockVLAPolicy
from robotic_surgery.learning_pipeline.retargeting.kinematic import KinematicRetargeter
from robotic_surgery.learning_pipeline.retargeting.representation import MockVisualEncoder
from robotic_surgery.learning_pipeline.types import FrameStack, RobotAction, RobotDemonstration


def test_representation_pretrain_reports_margin(clips):
    trainer = RepresentationTrainer(MockVisualEncoder())
    result = trainer.fit(clips, epochs=2)
    assert result.num_clips == len(clips)
    assert len(result.history) == 2
    assert -1.0 <= result.contrastive_margin <= 1.0


def test_vla_pretrain_then_finetune(clips):
    enc = MockVisualEncoder()
    pseudo = KinematicRetargeter().retarget_many(clips)
    policy = MockVLAPolicy(enc)
    policy.pretrain(pseudo, clips)
    assert policy.report.pretrain_transitions > 0

    # build a tiny real robot demo and finetune
    obs = [c.frames for c in clips[:1]]
    acts = [RobotAction(ee_pose=np.eye(4), gripper=0.0)]
    demo = RobotDemonstration("ep0", obs, acts, "pick up cup", success=True)
    report = policy.finetune([demo], epochs=2)
    assert report.finetune_transitions == 1

    action = policy.act(clips[0].frames, "pick up cup")
    assert isinstance(action, RobotAction)
    assert action.ee_pose.shape == (4, 4)


def test_untrained_policy_returns_safe_default():
    enc = MockVisualEncoder()
    policy = MockVLAPolicy(enc)
    stack = FrameStack(frames=np.zeros((1, 8, 8, 3), np.uint8), frame_indices=[0], sample_fps=1.0)
    action = policy.act(stack, "do something")
    assert action.gripper == 1.0  # open / no-op


def test_planner_decomposes_known_task():
    plan = HighLevelPlanner().plan("make coffee")
    assert plan.goal == "make coffee"
    assert len(plan.subtasks) >= 2
    assert any("cup" in s.instruction for s in plan.subtasks)


def test_planner_replan_inserts_retry():
    planner = HighLevelPlanner()
    plan = planner.plan("pour a drink")
    first = plan.subtasks[0]
    n_before = len(plan.subtasks)
    planner.replan(plan, first)
    assert first.status == "failed"
    assert len(plan.subtasks) == n_before + 1
