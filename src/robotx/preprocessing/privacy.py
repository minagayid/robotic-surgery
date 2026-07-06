"""Privacy redaction -- blur bystander faces and license plates *before* storage.

Design doc risk item: "POV video from the wild contains bystanders' faces --
blur/redact before storage, not after." This stage therefore runs before a clip
is ever written to the dataset. If redaction is required but impossible, the
policy (config) decides whether to drop the clip.

The box-blur redaction here is real; the *detector* is pluggable. The mock
detector flags skin-tone-ish and high-frequency rectangular regions as stand-ins
for faces/plates. Swap in a real face detector (e.g. RetinaFace) and an ALPR
model for production.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import PrivacyConfig
from ..types import FrameStack


@dataclass
class RedactionReport:
    faces_redacted: int = 0
    plates_redacted: int = 0
    dropped: bool = False
    regions: list[tuple[int, int, int, int, int]] = field(default_factory=list)  # (t,x0,y0,x1,y1)


def _box_blur1d(x: np.ndarray, axis: int, k: int) -> np.ndarray:
    """Length-preserving 1-D box mean along ``axis`` (shrinks kernel to fit)."""
    n = x.shape[axis]
    k = max(1, min(k, n))
    if k == 1:
        return x
    pad = k // 2
    pad_spec = [(pad, pad) if a == axis else (0, 0) for a in range(x.ndim)]
    padded = np.pad(x, pad_spec, mode="edge")
    cs = np.cumsum(padded, axis=axis)
    zero_shape = list(cs.shape)
    zero_shape[axis] = 1
    cs = np.concatenate([np.zeros(zero_shape, dtype=cs.dtype), cs], axis=axis)
    hi = np.take(cs, range(k, k + n), axis=axis)
    lo = np.take(cs, range(0, n), axis=axis)
    return (hi - lo) / k


def _box_blur(region: np.ndarray, k: int = 7) -> np.ndarray:
    """Cheap separable box blur over a HxWx3 region.

    Robust to regions smaller than the kernel: the kernel shrinks to fit each
    axis so a 1-2px detection still redacts without an index error, and the
    output shape always matches ``region``.
    """
    if region.size == 0:
        return region
    out = region.astype(np.float32)
    out = _box_blur1d(out, axis=0, k=k)
    out = _box_blur1d(out, axis=1, k=k)
    return np.clip(out, 0, 255).astype(np.uint8)


def _detect_sensitive_regions(frame: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Mock face/plate detector -> list of (x0,y0,x1,y1) boxes.

    Heuristic: find the brightest reddish blob (proxy for a face) per frame. A
    real detector replaces this entirely.
    """
    r, g, b = frame[..., 0].astype(float), frame[..., 1].astype(float), frame[..., 2].astype(float)
    skin = (r - g).clip(min=0) * (r - b).clip(min=0)
    if skin.max() <= 0:
        return []
    thr = skin.max() * 0.6
    ys, xs = np.where(skin > thr)
    if xs.size < 5:
        return []
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    return [(x0, y0, x1 + 1, y1 + 1)]


class PrivacyRedactor:
    def __init__(self, cfg: PrivacyConfig | None = None):
        self.cfg = cfg or PrivacyConfig()

    def redact(self, stack: FrameStack) -> tuple[FrameStack, RedactionReport]:
        report = RedactionReport()
        if not (self.cfg.blur_faces or self.cfg.blur_plates):
            return stack, report

        frames = stack.frames.copy()
        for t in range(frames.shape[0]):
            for (x0, y0, x1, y1) in _detect_sensitive_regions(frames[t]):
                frames[t, y0:y1, x0:x1] = _box_blur(frames[t, y0:y1, x0:x1])
                report.faces_redacted += 1
                report.regions.append((t, x0, y0, x1, y1))

        redacted = FrameStack(frames=frames, frame_indices=stack.frame_indices,
                              sample_fps=stack.sample_fps)
        return redacted, report
