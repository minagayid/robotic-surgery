"""Core data types shared across every stage of the Robotic Surgery pipeline.

These dataclasses are the *contracts* between layers. The design doc's
per-clip structured record --

    {frames, hand_pose_traj, object_tracks, depth, camera_pose, language_label}

-- is realised here as :class:`ClipRecord`. Everything downstream (retargeting,
learning, sim2real) consumes these types, so keeping them stable and
serialisable is what lets the heavy ML backends be swapped without touching
orchestration code.

All arrays are documented with their expected shapes. We keep numpy as the only
heavy dependency; arrays serialise to nested lists for JSON/manifest storage.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np

Array = np.ndarray


# --------------------------------------------------------------------------- #
# Provenance & licensing (Section 1 -- compliant sourcing)
# --------------------------------------------------------------------------- #
class SourceKind(str, Enum):
    """Where a clip legally came from. Drives what we are allowed to do with it."""

    OFFICIAL_API = "official_api"          # YouTube Data API, X API, Meta Graph, TikTok Research
    RESEARCH_DATASET = "research_dataset"  # Ego4D, EPIC-KITCHENS, SSv2, HowTo100M
    LICENSED_PARTNER = "licensed_partner"  # creator video licensed for AI training
    FIRST_PARTY = "first_party"            # we paid people to capture it (cleanest)


class LicenseStatus(str, Enum):
    CLEARED = "cleared"          # ok to train on
    RESEARCH_ONLY = "research_only"
    PENDING = "pending"          # not yet cleared -- must not reach training
    BLOCKED = "blocked"          # explicitly disallowed


@dataclass
class Provenance:
    """Immutable record of where a clip came from and what we may do with it."""

    source_kind: SourceKind
    source_id: str                       # e.g. dataset clip id or API video id
    license_status: LicenseStatus = LicenseStatus.PENDING
    attribution: Optional[str] = None
    consent_ref: Optional[str] = None    # ref to a signed consent form (first-party)
    retrieved_at: float = field(default_factory=time.time)

    @property
    def trainable(self) -> bool:
        return self.license_status in (LicenseStatus.CLEARED, LicenseStatus.RESEARCH_ONLY)


# --------------------------------------------------------------------------- #
# Raw / sampled video
# --------------------------------------------------------------------------- #
@dataclass
class VideoRef:
    """A handle to a source video plus its provenance. We do not hold pixels here."""

    uri: str                              # local path or storage URI
    provenance: Provenance
    fps: float = 30.0
    duration_s: float = 0.0
    width: int = 0
    height: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Shot:
    """A contiguous shot/scene after segmentation."""

    start_frame: int
    end_frame: int
    start_s: float
    end_s: float

    @property
    def num_frames(self) -> int:
        return self.end_frame - self.start_frame


@dataclass
class FrameStack:
    """Sampled frames for a clip. shape (T, H, W, 3), uint8, RGB."""

    frames: Array
    frame_indices: list[int]
    sample_fps: float

    def __post_init__(self) -> None:
        self.frames = np.asarray(self.frames)

    @property
    def num_frames(self) -> int:
        return int(self.frames.shape[0])


# --------------------------------------------------------------------------- #
# Per-clip extraction outputs (Section 2)
# --------------------------------------------------------------------------- #
@dataclass
class HandPoseTrajectory:
    """3D hand pose over time from monocular POV video (MediaPipe/HaMeR-style).

    joints: (T, 21, 3) -- 21 hand joints in camera frame (metres).
    wrist:  (T, 3)     -- convenience wrist position (== joints[:, 0]).
    handedness: 'left' | 'right' per hand; here we track the dominant hand.
    confidence: (T,) in [0, 1].
    """

    joints: Array
    handedness: str = "right"
    confidence: Optional[Array] = None

    def __post_init__(self) -> None:
        self.joints = np.asarray(self.joints, dtype=float)
        if self.confidence is None:
            self.confidence = np.ones(self.joints.shape[0])

    @property
    def wrist(self) -> Array:
        return self.joints[:, 0, :]


@dataclass
class CameraTrajectory:
    """Ego-motion of the POV camera (== wearer head) from SLAM/optical flow.

    poses: (T, 4, 4) homogeneous camera-to-world transforms.
    """

    poses: Array

    def __post_init__(self) -> None:
        self.poses = np.asarray(self.poses, dtype=float)

    @property
    def positions(self) -> Array:
        return self.poses[:, :3, 3]


@dataclass
class ObjectTrack:
    """A single tracked object across frames (Grounding DINO + SAM2 style)."""

    label: str
    track_id: int
    boxes: Array                 # (T, 4) xyxy in pixels; NaN where not visible
    score: float = 1.0
    contact_frame: Optional[int] = None   # frame where hand first contacts object

    def __post_init__(self) -> None:
        self.boxes = np.asarray(self.boxes, dtype=float)


@dataclass
class DepthMaps:
    """Monocular relative depth (Depth-Anything style). (T, H, W) float, larger=farther."""

    depth: Array

    def __post_init__(self) -> None:
        self.depth = np.asarray(self.depth, dtype=float)


@dataclass
class ActionSegment:
    """An atomic action localised in time, with a language description."""

    start_frame: int
    end_frame: int
    label: str                   # e.g. "pick up cup"
    score: float = 1.0


# --------------------------------------------------------------------------- #
# The structured per-clip record -- the pipeline's central artefact
# --------------------------------------------------------------------------- #
@dataclass
class ClipRecord:
    """Structured output per clip, per the design doc Section 2.

        {frames, hand_pose_traj, object_tracks, depth, camera_pose, language_label}
    """

    clip_id: str
    provenance: Provenance
    frames: FrameStack
    hand_pose: HandPoseTrajectory
    camera: CameraTrajectory
    object_tracks: list[ObjectTrack] = field(default_factory=list)
    depth: Optional[DepthMaps] = None
    actions: list[ActionSegment] = field(default_factory=list)
    language_label: str = ""
    quality_score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Lightweight, array-free summary for manifests and logging."""
        return {
            "clip_id": self.clip_id,
            "source_kind": self.provenance.source_kind.value,
            "license": self.provenance.license_status.value,
            "num_frames": self.frames.num_frames,
            "num_object_tracks": len(self.object_tracks),
            "num_actions": len(self.actions),
            "has_depth": self.depth is not None,
            "language_label": self.language_label,
            "quality_score": round(self.quality_score, 4),
        }


# --------------------------------------------------------------------------- #
# Retargeting outputs (Section 3)
# --------------------------------------------------------------------------- #
@dataclass
class RobotAction:
    """A single robot action / target at one timestep.

    ee_pose: (4, 4) target end-effector pose in robot base frame.
    gripper: scalar in [0, 1], 0 = closed, 1 = fully open.
    """

    ee_pose: Array
    gripper: float

    def __post_init__(self) -> None:
        self.ee_pose = np.asarray(self.ee_pose, dtype=float)
        if self.ee_pose.shape != (4, 4) or not np.isfinite(self.ee_pose).all():
            raise ValueError("ee_pose must be a finite 4x4 transform")
        gripper = float(self.gripper)
        if not np.isfinite(gripper):
            raise ValueError("gripper must be finite")
        self.gripper = float(np.clip(gripper, 0.0, 1.0))


@dataclass
class PseudoDemonstration:
    """A weak-supervision trajectory retargeted from human video (Section 3B).

    Marked ``weak=True`` because it is derived from noisy monocular pose with no
    depth ground truth -- to be used for pretraining / auxiliary loss, never as
    ground-truth robot actions.
    """

    clip_id: str
    actions: list[RobotAction]
    language_label: str = ""
    weak: bool = True
    confidence: float = 0.5

    @property
    def horizon(self) -> int:
        return len(self.actions)


@dataclass
class RobotDemonstration:
    """A *real* robot trajectory collected via teleop -- high-value ground truth."""

    episode_id: str
    observations: list[FrameStack]
    actions: list[RobotAction]
    language_instruction: str
    success: bool = True


# --------------------------------------------------------------------------- #
# Serialisation helpers
# --------------------------------------------------------------------------- #
def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses / numpy arrays / enums to JSON-safe data."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    return obj
