"""Frame sampling -- downsample a shot to the training frame rate (2-8 fps)."""

from __future__ import annotations

import numpy as np

from ..types import FrameStack, Shot, VideoRef


def sample_frames(
    frames: np.ndarray,
    shot: Shot,
    ref: VideoRef,
    target_fps: float = 4.0,
) -> FrameStack:
    """Uniformly sample a shot's frames down to ``target_fps``.

    Returns a :class:`FrameStack` holding the sampled frames plus their original
    frame indices (needed to align extractor outputs back to source time).
    """
    src_fps = ref.fps or 30.0
    step = max(1, int(round(src_fps / max(target_fps, 1e-6))))
    idxs = list(range(shot.start_frame, shot.end_frame, step))
    idxs = [i for i in idxs if i < frames.shape[0]]
    if not idxs:
        idxs = [shot.start_frame]
    sampled = frames[idxs]
    return FrameStack(frames=sampled, frame_indices=idxs, sample_fps=target_fps)
