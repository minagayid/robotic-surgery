"""Quality filtering -- drop blurry, low-res, or heavily occluded clips.

Real, dependency-free heuristics:
* blur    -- variance of a Laplacian-style high-pass (low variance = blurry).
* resolution -- min(H, W) against a floor.
* occlusion -- fraction of frames whose dynamic range collapses (a hand/object
  smothering the lens, lens-cap, motion smear).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..config import QualityConfig
from ..types import FrameStack


def _laplacian_var(gray: np.ndarray) -> float:
    """Variance of a discrete Laplacian -- classic focus/blur measure."""
    lap = (
        -4 * gray[1:-1, 1:-1]
        + gray[:-2, 1:-1] + gray[2:, 1:-1]
        + gray[1:-1, :-2] + gray[1:-1, 2:]
    )
    return float(lap.var())


@dataclass
class QualityReport:
    resolution: int
    blur: float          # 0 sharp .. 1 blurry
    occlusion: float     # fraction of frames occluded
    passed: bool
    reason: str = ""


class QualityFilter:
    def __init__(self, cfg: QualityConfig | None = None):
        self.cfg = cfg or QualityConfig()

    def assess(self, stack: FrameStack) -> QualityReport:
        frames = stack.frames
        h, w = frames.shape[1], frames.shape[2]
        resolution = min(h, w)
        gray = frames.mean(axis=-1)

        # blur: average focus measure across frames, mapped to [0,1] (1=blurry)
        focus = np.array([_laplacian_var(g) for g in gray])
        # normalise: ~<50 variance is blurry for 8-bit imagery
        blur = float(np.clip(1.0 - np.mean(focus) / 200.0, 0.0, 1.0))

        # occlusion: frames whose per-frame std is tiny (flat = lens blocked)
        stds = gray.reshape(gray.shape[0], -1).std(axis=1)
        occlusion = float(np.mean(stds < 5.0))

        passed, reason = True, "ok"
        if resolution < self.cfg.min_resolution:
            passed, reason = False, f"resolution<{self.cfg.min_resolution}"
        elif blur > self.cfg.max_blur:
            passed, reason = False, f"blur>{self.cfg.max_blur}"
        elif occlusion > self.cfg.max_occlusion:
            passed, reason = False, f"occlusion>{self.cfg.max_occlusion}"

        return QualityReport(resolution, round(blur, 4), round(occlusion, 4), passed, reason)
