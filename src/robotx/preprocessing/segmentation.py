"""Shot / scene segmentation.

Splits a long video into contiguous shots by detecting cuts as spikes in
frame-to-frame difference. This is a real, dependency-free implementation
(content-based cut detection) -- the same idea PySceneDetect uses, just compact.
"""

from __future__ import annotations

import numpy as np

from ..types import Shot, VideoRef


def _frame_diffs(frames: np.ndarray) -> np.ndarray:
    """Mean absolute difference between consecutive frames, normalised to [0,1]."""
    if frames.shape[0] < 2:
        return np.zeros(0)
    gray = frames.mean(axis=-1)
    d = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    return d / 255.0


def segment_shots(
    frames: np.ndarray,
    ref: VideoRef,
    threshold: float = 0.12,
    min_shot_frames: int = 8,
) -> list[Shot]:
    """Detect shot boundaries via content-based cut detection.

    A cut is declared where the normalised inter-frame difference exceeds
    ``threshold`` *and* stands out from the local baseline. Shots shorter than
    ``min_shot_frames`` are merged forward.
    """
    n = frames.shape[0]
    if n == 0:
        return []
    diffs = _frame_diffs(frames)
    # adaptive: a cut must exceed both an absolute threshold and 3x local median
    if diffs.size:
        baseline = np.median(diffs) if np.median(diffs) > 0 else 1e-6
        cut_mask = (diffs > threshold) & (diffs > 3 * baseline)
        cut_frames = [int(i) + 1 for i in np.where(cut_mask)[0]]
    else:
        cut_frames = []

    boundaries = [0] + cut_frames + [n]
    boundaries = sorted(set(boundaries))

    shots: list[Shot] = []
    fps = ref.fps or 30.0
    start = boundaries[0]
    for b in boundaries[1:]:
        if b - start < min_shot_frames and b != n:
            continue  # merge tiny shots forward
        shots.append(Shot(start_frame=start, end_frame=b,
                           start_s=start / fps, end_s=b / fps))
        start = b
    if not shots:  # whole clip is one shot
        shots = [Shot(0, n, 0.0, n / fps)]
    return shots
