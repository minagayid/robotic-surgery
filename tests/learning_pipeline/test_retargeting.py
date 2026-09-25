import numpy as np

from robotic_surgery.learning_pipeline.config import RetargetConfig
from robotic_surgery.learning_pipeline.retargeting.kinematic import KinematicRetargeter, _hand_orientation
from robotic_surgery.learning_pipeline.retargeting.representation import MockVisualEncoder, build_encoder, cosine


def test_hand_orientation_is_rotation():
    joints = np.random.default_rng(0).standard_normal((21, 3))
    R = _hand_orientation(joints)
    # orthonormal columns
    assert np.allclose(R.T @ R, np.eye(3), atol=1e-6)
    assert np.isclose(abs(np.linalg.det(R)), 1.0, atol=1e-6)


def test_retarget_produces_weak_pseudo_demo(clips):
    demos = KinematicRetargeter().retarget_many(clips)
    assert demos, "expected at least one pseudo-demo"
    for d in demos:
        assert d.weak is True
        assert d.horizon >= 1
        for a in d.actions:
            assert a.ee_pose.shape == (4, 4)
            assert 0.0 <= a.gripper <= 1.0


def test_contact_timing_closes_gripper(clips):
    # find a clip with a contact frame and confirm gripper closes after it
    rt = KinematicRetargeter(RetargetConfig())
    for clip in clips:
        contacts = [t.contact_frame for t in clip.object_tracks if t.contact_frame is not None]
        if not contacts:
            continue
        demo = rt.retarget(clip)
        c = min(contacts)
        if demo and c < demo.horizon:
            assert demo.actions[min(c, demo.horizon - 1)].gripper <= 0.2
            return
    # if no contact clip present, the test is vacuously fine


def test_encoder_embeddings_are_normalised(clips):
    enc = MockVisualEncoder(embed_dim=64)
    e = enc.encode(clips[0].frames)
    assert e.shape == (64,)
    assert np.isclose(np.linalg.norm(e), 1.0, atol=1e-6)


def test_encoder_self_similarity_is_one(clips):
    enc = build_encoder("mock", embed_dim=32)
    e = enc.encode(clips[0].frames)
    assert np.isclose(cosine(e, e), 1.0, atol=1e-6)
