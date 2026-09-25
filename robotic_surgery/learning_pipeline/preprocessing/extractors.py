"""Per-clip extractors (design doc Section 2).

Each extractor is an interface with a deterministic ``mock`` implementation so
the pipeline plumbing runs offline. The docstrings identify possible future
models and required outputs; no real model backend is included. Selection is driven by
:class:`~robotic_surgery.learning_pipeline.config.BackendConfig`.

Extractors
----------
* :class:`HandPoseEstimator`     -- MediaPipe Hands / FrankMocap / HaMeR
* :class:`EgoMotionEstimator`    -- optical-flow / SLAM ego-motion
* :class:`ObjectTrackerDetector` -- Grounding DINO (open-vocab) + SAM2 tracking
* :class:`DepthEstimator`        -- Depth-Anything monocular depth
* :class:`ActionSegmenter`       -- temporal action localisation
* :class:`LanguageGrounder`      -- VLM captioner -> task description
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..config import BackendConfig
from ..types import (
    ActionSegment,
    CameraTrajectory,
    DepthMaps,
    FrameStack,
    HandPoseTrajectory,
    ObjectTrack,
)

_ATOMIC_ACTIONS = [
    "reach for object", "pick up cup", "pour liquid", "place object",
    "open drawer", "wipe surface", "stir contents", "put down object",
]


def _seed_of(stack: FrameStack) -> int:
    """Deterministic seed from frame content so mock outputs are reproducible."""
    return int(abs(hash(stack.frames.sum().item())) % (2**31))


# --------------------------------------------------------------------------- #
# Hand pose
# --------------------------------------------------------------------------- #
class HandPoseEstimator(ABC):
    @abstractmethod
    def estimate(self, stack: FrameStack) -> HandPoseTrajectory: ...


class MockHandPose(HandPoseEstimator):
    """Deterministic 21-joint hand trajectory tracing the frame's bright blob.

    Candidate future backends: MediaPipe Hands or HaMeR; none is integrated.
    """

    def estimate(self, stack: FrameStack) -> HandPoseTrajectory:
        frames = stack.frames
        T = frames.shape[0]
        h, w = frames.shape[1], frames.shape[2]
        joints = np.zeros((T, 21, 3))
        conf = np.zeros(T)
        for t in range(T):
            r = frames[t, ..., 0].astype(float) - frames[t, ..., 2].astype(float)
            if r.max() > 0:
                yx = np.unravel_index(np.argmax(r), r.shape)
                cy, cx = yx
                conf[t] = float(np.clip(r.max() / 90.0, 0, 1))
            else:
                cy, cx = h / 2, w / 2
                conf[t] = 0.1
            # wrist in normalised camera coords, ~0.5 m in front
            wrist = np.array([cx / w - 0.5, cy / h - 0.5, 0.5])
            joints[t, 0] = wrist
            # fingertips fan out; finger spread encodes grip (closes over time)
            spread = 0.04 * (1.0 - 0.5 * t / max(T - 1, 1))
            for j in range(1, 21):
                ang = 2 * np.pi * j / 20
                joints[t, j] = wrist + np.array([np.cos(ang), np.sin(ang), 0.0]) * spread
        return HandPoseTrajectory(joints=joints, handedness="right", confidence=conf)


# --------------------------------------------------------------------------- #
# Ego-motion
# --------------------------------------------------------------------------- #
class EgoMotionEstimator(ABC):
    @abstractmethod
    def estimate(self, stack: FrameStack) -> CameraTrajectory: ...


class MockEgoMotion(EgoMotionEstimator):
    """Integrates coarse optical flow into a camera-to-world trajectory.

    Candidate future backends include DROID-SLAM or optical-flow VO. Here we estimate a
    global translation per frame from the mean flow direction of the gradient.
    """

    def estimate(self, stack: FrameStack) -> CameraTrajectory:
        frames = stack.frames.mean(axis=-1)
        T = frames.shape[0]
        poses = np.tile(np.eye(4), (T, 1, 1))
        pos = np.zeros(3)
        for t in range(1, T):
            diff = frames[t] - frames[t - 1]
            # crude flow proxy: horizontal/vertical brightness shift
            dx = float(np.sign(diff[:, 1:].mean() - diff[:, :-1].mean())) * 0.01
            dy = float(np.sign(diff[1:, :].mean() - diff[:-1, :].mean())) * 0.01
            pos = pos + np.array([dx, dy, 0.005])  # slow forward drift
            poses[t, :3, 3] = pos
        return CameraTrajectory(poses=poses)


# --------------------------------------------------------------------------- #
# Detection + tracking
# --------------------------------------------------------------------------- #
class ObjectTrackerDetector(ABC):
    @abstractmethod
    def track(self, stack: FrameStack, hand: HandPoseTrajectory) -> list[ObjectTrack]: ...


class MockObjectTracker(ObjectTrackerDetector):
    """Emits one or two tracked objects with a hand-contact frame.

    Candidate future components include Grounding DINO and SAM2; the mock propagates
    masks across frames; contact_frame is where the hand box meets the object.
    """

    def track(self, stack: FrameStack, hand: HandPoseTrajectory) -> list[ObjectTrack]:
        T = stack.frames.num_frames if hasattr(stack.frames, "num_frames") else stack.frames.shape[0]
        h, w = stack.frames.shape[1], stack.frames.shape[2]
        rng = np.random.default_rng(_seed_of(stack))
        n_obj = int(rng.integers(1, 3))
        labels = rng.choice(["cup", "bottle", "plate", "drawer", "cloth"], size=n_obj, replace=False)
        tracks: list[ObjectTrack] = []
        wrist_px = np.stack([
            (hand.wrist[:, 0] + 0.5) * w,
            (hand.wrist[:, 1] + 0.5) * h,
        ], axis=1)
        for i, label in enumerate(labels):
            cx = float(rng.uniform(0.3, 0.7)) * w
            cy = float(rng.uniform(0.3, 0.7)) * h
            boxes = np.tile([cx - 15, cy - 15, cx + 15, cy + 15], (T, 1)).astype(float)
            # contact when wrist is nearest the object centre
            dists = np.linalg.norm(wrist_px - np.array([cx, cy]), axis=1)
            contact = int(np.argmin(dists)) if i == 0 else None
            tracks.append(ObjectTrack(label=str(label), track_id=i, boxes=boxes,
                                      score=0.9, contact_frame=contact))
        return tracks


# --------------------------------------------------------------------------- #
# Depth
# --------------------------------------------------------------------------- #
class DepthEstimator(ABC):
    @abstractmethod
    def estimate(self, stack: FrameStack) -> DepthMaps: ...


class MockDepth(DepthEstimator):
    """Relative depth proxy from image intensity (brighter ~ nearer).

    A candidate future backend is Depth-Anything-V2. The mock relative depth
    video has no depth channel, so this is always an *estimate* -- consumed as
    weak structure, never metric ground truth.
    """

    def estimate(self, stack: FrameStack) -> DepthMaps:
        gray = stack.frames.mean(axis=-1) / 255.0
        depth = 1.0 - gray  # invert: bright=near
        return DepthMaps(depth=depth)


# --------------------------------------------------------------------------- #
# Action segmentation
# --------------------------------------------------------------------------- #
class ActionSegmenter(ABC):
    @abstractmethod
    def segment(self, stack: FrameStack, hand: HandPoseTrajectory) -> list[ActionSegment]: ...


class MockActionSegmenter(ActionSegmenter):
    """Chops a clip into atomic actions at hand-velocity minima.

    A candidate future model is ActionFormer. Here
    we split where wrist speed dips (reach/settle boundaries) and label segments.
    """

    def segment(self, stack: FrameStack, hand: HandPoseTrajectory) -> list[ActionSegment]:
        T = hand.wrist.shape[0]
        if T < 2:
            return [ActionSegment(0, max(T, 1), _ATOMIC_ACTIONS[0], 0.5)]
        speed = np.linalg.norm(np.diff(hand.wrist, axis=0), axis=1)
        # boundaries at local minima of speed
        bounds = [0]
        for t in range(1, len(speed) - 1):
            if speed[t] < speed[t - 1] and speed[t] < speed[t + 1] and speed[t] < speed.mean() * 0.5:
                if t - bounds[-1] >= 2:
                    bounds.append(t)
        bounds.append(T)
        rng = np.random.default_rng(_seed_of(stack))
        segs: list[ActionSegment] = []
        for i in range(len(bounds) - 1):
            label = _ATOMIC_ACTIONS[int(rng.integers(0, len(_ATOMIC_ACTIONS)))]
            segs.append(ActionSegment(bounds[i], bounds[i + 1], label, 0.7))
        return segs


# --------------------------------------------------------------------------- #
# Language grounding
# --------------------------------------------------------------------------- #
class LanguageGrounder(ABC):
    @abstractmethod
    def caption(self, stack: FrameStack, actions: list[ActionSegment],
                tracks: list[ObjectTrack]) -> str: ...


class MockLanguageGrounder(LanguageGrounder):
    """Composes a task description from action + object context.

    Candidate future models include LLaVA and Qwen-VL; the mock caption is
    what lets a language-conditioned policy later use the clip.
    """

    def caption(self, stack, actions, tracks) -> str:
        obj = tracks[0].label if tracks else "object"
        if actions:
            verb = actions[0].label.split()[0]
            return f"{verb} the {obj}"
        return f"manipulate the {obj}"


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
_REGISTRY = {
    "hand_pose": {"mock": MockHandPose},
    "egomotion": {"mock": MockEgoMotion},
    "tracker": {"mock": MockObjectTracker},
    "depth": {"mock": MockDepth},
    "action_seg": {"mock": MockActionSegmenter},
    "captioner": {"mock": MockLanguageGrounder},
}


def _pick(kind: str, name: str):
    backends = _REGISTRY[kind]
    if name not in backends:
        raise NotImplementedError(
            f"Backend {name!r} for {kind!r} has no registered implementation. "
            f"Only {sorted(backends)} are available in this build. Optional "
            "model dependencies do not provide an integration by themselves."
        )
    return backends[name]()


def build_extractors(cfg: BackendConfig) -> dict[str, object]:
    """Instantiate the extractor set selected by ``cfg``."""
    return {
        "hand_pose": _pick("hand_pose", cfg.hand_pose),
        "egomotion": _pick("egomotion", cfg.egomotion),
        "tracker": _pick("tracker", cfg.tracker),
        "depth": _pick("depth", cfg.depth),
        "action_seg": _pick("action_seg", cfg.action_seg),
        "captioner": _pick("captioner", cfg.captioner),
    }
