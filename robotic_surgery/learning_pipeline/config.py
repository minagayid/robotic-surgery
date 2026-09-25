"""Configuration for the Robotic Surgery pipeline.

A single dataclass tree drives the whole pipeline so that behaviour is
reproducible and diffable. Load from YAML with :func:`load_config`; every field
has a sensible default so an empty config still runs end-to-end on mock
backends.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BackendConfig:
    """Selects the implementation for each pluggable ML component.

    Only ``"mock"`` backends are implemented here. The other names below are
    configuration placeholders; installing optional model dependencies does
    not add integrations or make them usable.
    """

    hand_pose: str = "mock"          # other names are placeholders only
    egomotion: str = "mock"
    detector: str = "mock"
    tracker: str = "mock"
    depth: str = "mock"
    action_seg: str = "mock"
    captioner: str = "mock"
    encoder: str = "mock"
    policy: str = "mock"
    planner: str = "mock"


@dataclass
class SamplingConfig:
    target_fps: float = 4.0          # design doc: 2-8 fps
    min_shot_frames: int = 8


@dataclass
class QualityConfig:
    min_resolution: int = 240        # min(height, width)
    max_blur: float = 0.6            # reject clips blurrier than this (0=sharp,1=blur)
    max_occlusion: float = 0.5


@dataclass
class PrivacyConfig:
    blur_faces: bool = True
    blur_plates: bool = True
    drop_if_unredactable: bool = True   # if we can't redact, drop rather than store


@dataclass
class RetargetConfig:
    # embodiment gap: fixed wrist -> end-effector offset (metres, robot base frame)
    wrist_to_ee_offset: tuple[float, float, float] = (0.0, 0.0, -0.03)
    gripper_open_dist: float = 0.08     # fingertip distance mapped to fully open
    gripper_closed_dist: float = 0.02   # fingertip distance mapped to fully closed
    min_confidence: float = 0.3


@dataclass
class SafetyConfig:
    """Limits for the toy simulator only; these are not hardware safety settings."""

    max_ee_speed_m_s: float = 0.15
    max_gripper_closure_fraction: float = 0.25

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_ee_speed_m_s) or self.max_ee_speed_m_s <= 0.0:
            raise ValueError("max_ee_speed_m_s must be finite and positive")
        if (
            not math.isfinite(self.max_gripper_closure_fraction)
            or not 0.0 <= self.max_gripper_closure_fraction <= 1.0
        ):
            raise ValueError("max_gripper_closure_fraction must be between 0 and 1")


@dataclass
class OpsConfig:
    dedup_threshold: float = 0.98       # cosine sim above which clips are near-duplicates
    enable_bias_filter: bool = True
    enable_safety_filter: bool = True


@dataclass
class PipelineConfig:
    seed: int = 0
    workdir: str = "outputs"
    backends: BackendConfig = field(default_factory=BackendConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    retarget: RetargetConfig = field(default_factory=RetargetConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    ops: OpsConfig = field(default_factory=OpsConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _merge(dc: Any, data: dict[str, Any]) -> Any:
    """Recursively overlay ``data`` onto a dataclass instance ``dc``."""
    if not hasattr(dc, "__dataclass_fields__"):
        return data
    fields = dc.__dataclass_fields__
    for key, value in data.items():
        if key not in fields:
            raise KeyError(f"Unknown config key: {key!r} (in {type(dc).__name__})")
        current = getattr(dc, key)
        if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
            setattr(dc, key, _merge(current, value))
        elif isinstance(current, tuple) and isinstance(value, list):
            setattr(dc, key, tuple(value))
        else:
            setattr(dc, key, value)
    return dc


def load_config(path: str | Path | None = None) -> PipelineConfig:
    """Load a :class:`PipelineConfig`, overlaying YAML at ``path`` if given."""
    cfg = PipelineConfig()
    if path is None:
        return cfg
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    data = yaml.safe_load(p.read_text()) or {}
    return _merge(cfg, data)


def dump_config(cfg: PipelineConfig, path: str | Path) -> None:
    Path(path).write_text(yaml.safe_dump(cfg.to_dict(), sort_keys=False))
