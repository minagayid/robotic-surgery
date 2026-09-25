import numpy as np
import pytest

from robotic_surgery.learning_pipeline.config import PipelineConfig, dump_config, load_config
from robotic_surgery.learning_pipeline.types import (
    HandPoseTrajectory,
    LicenseStatus,
    Provenance,
    RobotAction,
    SourceKind,
    to_jsonable,
)


def test_provenance_trainable_flags():
    cleared = Provenance(SourceKind.FIRST_PARTY, "x", LicenseStatus.CLEARED)
    pending = Provenance(SourceKind.OFFICIAL_API, "y", LicenseStatus.PENDING)
    assert cleared.trainable
    assert not pending.trainable


def test_robot_action_clamps_gripper():
    a = RobotAction(ee_pose=np.eye(4), gripper=5.0)
    assert a.gripper == 1.0
    b = RobotAction(ee_pose=np.eye(4), gripper=-2.0)
    assert b.gripper == 0.0


def test_robot_action_rejects_malformed_pose_and_non_finite_gripper():
    with pytest.raises(ValueError, match="finite 4x4"):
        RobotAction(ee_pose=np.zeros((3, 3)), gripper=0.5)
    with pytest.raises(ValueError, match="gripper must be finite"):
        RobotAction(ee_pose=np.eye(4), gripper=np.nan)


def test_hand_pose_defaults_confidence():
    hp = HandPoseTrajectory(joints=np.zeros((4, 21, 3)))
    assert hp.confidence.shape == (4,)
    assert np.allclose(hp.wrist, hp.joints[:, 0, :])


def test_to_jsonable_handles_arrays_enums():
    data = to_jsonable({"a": np.arange(3), "k": SourceKind.FIRST_PARTY})
    assert data["a"] == [0, 1, 2]
    assert data["k"] == "first_party"


def test_config_roundtrip(tmp_path):
    cfg = PipelineConfig()
    cfg.sampling.target_fps = 6.0
    cfg.safety.max_ee_speed_m_s = 0.2
    p = tmp_path / "cfg.yaml"
    dump_config(cfg, p)
    loaded = load_config(p)
    assert loaded.sampling.target_fps == 6.0
    assert loaded.safety.max_ee_speed_m_s == 0.2


def test_config_rejects_unknown_key(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("nonsense_key: 1\n")
    with pytest.raises(KeyError):
        load_config(p)
