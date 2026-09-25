"""Video reading.

The real reader decodes the file/stream referenced by a :class:`VideoRef` (via
PyAV / OpenCV) into an RGB frame array. The mock reader synthesises
deterministic frames from the ref's seed so the pipeline is fully runnable and
testable without any video files or codecs installed.
"""

from __future__ import annotations

import numpy as np

from ..types import VideoRef


def read_frames(ref: VideoRef, max_frames: int | None = None) -> np.ndarray:
    """Return frames as (T, H, W, 3) uint8 RGB.

    Mock implementation: renders a moving gradient + a moving "hand" blob so that
    downstream heuristics (blur/quality, optical-flow ego-motion) have real
    structure to operate on. Deterministic in ``ref``'s seed.
    """
    seed = int(ref.metadata.get("seed", 0))
    rng = np.random.default_rng(seed)
    # Render at a resolution that clears realistic quality floors (>=240px) while
    # staying cheap. Real decoders return the source resolution; the mock keeps a
    # sane cap so a batch of clips stays in memory.
    h = min(ref.height or 480, 240)
    w = min(ref.width or 640, 320)
    n_total = max(1, int(ref.duration_s * ref.fps))
    n = min(n_total, max_frames or n_total, 60)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    frames = np.empty((n, h, w, 3), dtype=np.uint8)
    hand_x0, hand_y0 = rng.uniform(0.2, 0.4, size=2) * [w, h]
    dx, dy = rng.uniform(-1.5, 1.5, size=2)
    for t in range(n):
        base = (np.sin((xx + t * 2) * 0.05) + np.cos((yy + t) * 0.05)) * 50 + 128
        # high-frequency texture so focus/blur heuristics see real detail
        texture = rng.normal(0, 18, size=(h, w))
        base = base + texture
        img = np.stack([base, base * 0.9, base * 0.8], axis=-1)
        # a moving skin-tone blob standing in for the hand
        cx, cy = hand_x0 + dx * t, hand_y0 + dy * t
        blob = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 20.0**2)))
        img[..., 0] += blob * 110
        img[..., 1] += blob * 55
        frames[t] = np.clip(img, 0, 255).astype(np.uint8)
    return frames
