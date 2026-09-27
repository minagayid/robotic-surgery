"""Dataset versioning & embedding-based dedup.

Exact dedup lives in the manifest (content hash). This adds *near*-dedup via the
visual encoder: clips whose embeddings exceed ``dedup_threshold`` cosine
similarity are treated as duplicates and dropped, keeping the highest-quality
representative. Every accepted change bumps the manifest version.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import OpsConfig
from ..data.manifest import DatasetManifest
from ..retargeting.representation import VisualEncoder, cosine
from ..types import ClipRecord


@dataclass
class DedupResult:
    kept: list[str] = field(default_factory=list)
    dropped: dict[str, str] = field(default_factory=dict)   # clip_id -> representative id

    @property
    def num_kept(self) -> int:
        return len(self.kept)


class DatasetVersioner:
    def __init__(self, encoder: VisualEncoder, cfg: OpsConfig | None = None,
                 manifest: DatasetManifest | None = None):
        self.encoder = encoder
        self.cfg = cfg or OpsConfig()
        self.manifest = manifest or DatasetManifest()

    def near_dedup(self, clips: list[ClipRecord]) -> tuple[list[ClipRecord], DedupResult]:
        result = DedupResult()
        kept: list[ClipRecord] = []
        kept_embeds: list[np.ndarray] = []
        # process highest-quality clips first so they become representatives
        for clip in sorted(clips, key=lambda c: c.quality_score, reverse=True):
            emb = self.encoder.encode(clip.frames)
            dup_of = None
            for rep_clip, rep_emb in zip(kept, kept_embeds):
                if cosine(emb, rep_emb) >= self.cfg.dedup_threshold:
                    dup_of = rep_clip.clip_id
                    break
            if dup_of is None:
                kept.append(clip)
                kept_embeds.append(emb)
                result.kept.append(clip.clip_id)
            else:
                result.dropped[clip.clip_id] = dup_of
        return kept, result

    def commit(self, clips: list[ClipRecord]) -> dict:
        """Dedup then add survivors to the manifest, bumping its version."""
        deduped, dedup = self.near_dedup(clips)
        stats = self.manifest.add_many(deduped)
        stats["near_duplicates"] = len(dedup.dropped)
        return stats
