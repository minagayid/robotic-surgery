"""Approach B -- explicit kinematic retargeting to a pseudo-demonstration.

Maps the estimated human hand trajectory onto the robot's end-effector frame,
accounting for the embodiment gap:

* **wrist pose -> end-effector pose** with a fixed offset (a stand-in for a full
  IK solve; the offset absorbs the human-hand vs robot-gripper geometry gap).
* **finger pose -> gripper open/close** from thumb-index fingertip distance.
* **approach/contact timing** aligned to the object track's contact frame.

The output is a :class:`PseudoDemonstration`, explicitly flagged ``weak`` because
it comes from noisy monocular pose with no depth ground truth -- for pretraining
/ auxiliary loss, never as ground-truth robot actions.
"""

from __future__ import annotations

import numpy as np

from ..config import RetargetConfig
from ..types import ClipRecord, HandPoseTrajectory, PseudoDemonstration, RobotAction


def _hand_orientation(joints_t: np.ndarray) -> np.ndarray:
    """Build a 3x3 rotation for the hand from its joints at one timestep.

    x-axis: wrist -> mean fingertip (pointing direction)
    z-axis: palm normal (from two spanning finger vectors)
    y-axis: z cross x (right-handed)
    Falls back to identity when the hand is degenerate.
    """
    wrist = joints_t[0]
    fingers = joints_t[1:]
    x = fingers.mean(axis=0) - wrist
    if np.linalg.norm(x) < 1e-6:
        return np.eye(3)
    x = x / np.linalg.norm(x)
    v1 = fingers[0] - wrist
    v2 = fingers[len(fingers) // 2] - wrist
    z = np.cross(v1, v2)
    if np.linalg.norm(z) < 1e-6:
        # pick any vector orthogonal to x
        z = np.cross(x, np.array([0.0, 0.0, 1.0]))
        if np.linalg.norm(z) < 1e-6:
            z = np.cross(x, np.array([0.0, 1.0, 0.0]))
    z = z / np.linalg.norm(z)
    y = np.cross(z, x)
    y = y / (np.linalg.norm(y) + 1e-9)
    z = np.cross(x, y)
    return np.stack([x, y, z], axis=1)  # columns are the axes


def _gripper_from_fingers(joints_t: np.ndarray, cfg: RetargetConfig) -> float:
    """Map thumb-tip to index-tip distance onto gripper opening in [0,1].

    In the 21-joint layout, index 4 is the thumb tip and 8 the index tip (the
    MediaPipe convention). The mock 20-fan collapses gracefully via clip.
    """
    thumb = joints_t[4] if joints_t.shape[0] > 4 else joints_t[-1]
    index = joints_t[8] if joints_t.shape[0] > 8 else joints_t[1]
    dist = float(np.linalg.norm(thumb - index))
    lo, hi = cfg.gripper_closed_dist, cfg.gripper_open_dist
    return float(np.clip((dist - lo) / max(hi - lo, 1e-6), 0.0, 1.0))


class KinematicRetargeter:
    def __init__(self, cfg: RetargetConfig | None = None):
        self.cfg = cfg or RetargetConfig()

    def retarget(self, clip: ClipRecord) -> PseudoDemonstration | None:
        hand = clip.hand_pose
        T = hand.joints.shape[0]
        if T == 0:
            return None

        offset = np.asarray(self.cfg.wrist_to_ee_offset, dtype=float)
        actions: list[RobotAction] = []
        confidences: list[float] = []

        for t in range(T):
            if hand.confidence[t] < self.cfg.min_confidence:
                # low-confidence frames: hold previous pose (or skip if first)
                if actions:
                    actions.append(actions[-1])
                    confidences.append(hand.confidence[t])
                continue
            R = _hand_orientation(hand.joints[t])
            wrist = hand.wrist[t]
            ee_pos = wrist + R @ offset            # offset applied in wrist frame
            ee_pose = np.eye(4)
            ee_pose[:3, :3] = R
            ee_pose[:3, 3] = ee_pos
            gripper = _gripper_from_fingers(hand.joints[t], self.cfg)
            actions.append(RobotAction(ee_pose=ee_pose, gripper=gripper))
            confidences.append(hand.confidence[t])

        if not actions:
            return None

        # snap gripper to close at the object-contact frame (approach/contact timing)
        self._apply_contact_timing(clip, actions)

        conf = float(np.mean(confidences)) if confidences else 0.0
        return PseudoDemonstration(
            clip_id=clip.clip_id,
            actions=actions,
            language_label=clip.language_label,
            weak=True,
            confidence=round(conf, 4),
        )

    def _apply_contact_timing(self, clip: ClipRecord, actions: list[RobotAction]) -> None:
        """Force gripper closure from the contact frame onward for grasped objects."""
        contact = None
        for trk in clip.object_tracks:
            if trk.contact_frame is not None:
                contact = trk.contact_frame if contact is None else min(contact, trk.contact_frame)
        if contact is None:
            return
        contact = int(np.clip(contact, 0, len(actions) - 1))
        for t in range(contact, len(actions)):
            # bias toward closed after contact (grasp), preserving pose
            actions[t] = RobotAction(ee_pose=actions[t].ee_pose,
                                     gripper=min(actions[t].gripper, 0.2))

    def retarget_many(self, clips: list[ClipRecord]) -> list[PseudoDemonstration]:
        out = []
        for c in clips:
            demo = self.retarget(c)
            if demo is not None:
                out.append(demo)
        return out
