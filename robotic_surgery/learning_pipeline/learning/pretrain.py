"""Measure a temporal embedding statistic for mock clips.

This module computes adjacent/far-frame cosine similarities over the encoder's
fixed mock embeddings. It does not optimize encoder weights, train a model, or
write checkpoints. A research objective is not a working trainer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..retargeting.representation import VisualEncoder, cosine
from ..types import ClipRecord


@dataclass
class PretrainResult:
    num_clips: int
    embed_dim: int
    temporal_alignment: float          # mean cosine of adjacent-frame embeds (higher=better)
    negative_similarity: float         # mean cosine of far-apart embeds (lower=better)
    contrastive_margin: float          # temporal_alignment - negative_similarity
    history: list[float] = field(default_factory=list)


class RepresentationTrainer:
    """Runs the pretraining objective and reports representation quality."""

    def __init__(self, encoder: VisualEncoder):
        self.encoder = encoder

    def _clip_alignment(self, clip: ClipRecord) -> tuple[float, float]:
        embeds = self.encoder.encode_frames(clip.frames)
        if embeds.shape[0] < 3:
            return 1.0, 0.0
        pos = np.mean([cosine(embeds[t], embeds[t + 1]) for t in range(len(embeds) - 1)])
        # negatives: pair each frame with the temporally farthest one
        neg = np.mean([cosine(embeds[t], embeds[-1 - t]) for t in range(len(embeds) // 2)])
        return float(pos), float(neg)

    def fit(self, clips: list[ClipRecord], epochs: int = 1) -> PretrainResult:
        if not clips:
            return PretrainResult(0, self.encoder.embed_dim, 0.0, 0.0, 0.0)
        history: list[float] = []
        pos_m = neg_m = 0.0
        for _ in range(max(epochs, 1)):
            pos_vals, neg_vals = [], []
            for clip in clips:
                p, n = self._clip_alignment(clip)
                pos_vals.append(p)
                neg_vals.append(n)
            pos_m, neg_m = float(np.mean(pos_vals)), float(np.mean(neg_vals))
            history.append(pos_m - neg_m)
        return PretrainResult(
            num_clips=len(clips),
            embed_dim=self.encoder.embed_dim,
            temporal_alignment=round(pos_m, 4),
            negative_similarity=round(neg_m, 4),
            contrastive_margin=round(pos_m - neg_m, 4),
            history=history,
        )
