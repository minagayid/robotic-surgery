"""Assembles a :class:`VideoRef` into structured :class:`ClipRecord` s.

Ties the whole of Section 2 together: read -> segment -> per-shot sample ->
quality filter -> privacy redact -> extract everything -> ClipRecord.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import PipelineConfig
from ..types import ClipRecord, VideoRef
from .extractors import build_extractors
from .io import read_frames
from .privacy import PrivacyRedactor
from .quality import QualityFilter
from .sampling import sample_frames
from .segmentation import segment_shots


@dataclass
class BuildStats:
    shots: int = 0
    clips_built: int = 0
    rejected_quality: int = 0
    dropped_privacy: int = 0
    reasons: list[str] = field(default_factory=list)


class ClipBuilder:
    def __init__(self, cfg: PipelineConfig):
        self.cfg = cfg
        self.quality = QualityFilter(cfg.quality)
        self.privacy = PrivacyRedactor(cfg.privacy)
        self.extractors = build_extractors(cfg.backends)

    def build(self, ref: VideoRef) -> tuple[list[ClipRecord], BuildStats]:
        stats = BuildStats()
        frames = read_frames(ref)
        shots = segment_shots(frames, ref, min_shot_frames=self.cfg.sampling.min_shot_frames)
        stats.shots = len(shots)

        clips: list[ClipRecord] = []
        for si, shot in enumerate(shots):
            stack = sample_frames(frames, shot, ref, self.cfg.sampling.target_fps)

            q = self.quality.assess(stack)
            if not q.passed:
                stats.rejected_quality += 1
                stats.reasons.append(f"shot{si}:quality:{q.reason}")
                continue

            stack, redaction = self.privacy.redact(stack)
            if redaction.dropped:
                stats.dropped_privacy += 1
                stats.reasons.append(f"shot{si}:privacy:unredactable")
                continue

            clip = self._extract(ref, si, stack, q.blur)
            clips.append(clip)
            stats.clips_built += 1
        return clips, stats

    def _extract(self, ref: VideoRef, shot_idx: int, stack, blur: float) -> ClipRecord:
        ex = self.extractors
        hand = ex["hand_pose"].estimate(stack)
        camera = ex["egomotion"].estimate(stack)
        tracks = ex["tracker"].track(stack, hand)
        depth = ex["depth"].estimate(stack)
        actions = ex["action_seg"].segment(stack, hand)
        label = ex["captioner"].caption(stack, actions, tracks)

        clip_id = f"{ref.provenance.source_id}#shot{shot_idx}"
        return ClipRecord(
            clip_id=clip_id,
            provenance=ref.provenance,
            frames=stack,
            hand_pose=hand,
            camera=camera,
            object_tracks=tracks,
            depth=depth,
            actions=actions,
            language_label=label,
            quality_score=round(1.0 - blur, 4),
            metadata={"source_uri": ref.uri},
        )
