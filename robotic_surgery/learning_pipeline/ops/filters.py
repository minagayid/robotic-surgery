"""Dataset filters -- action-safety and bias, per the design's risk section.

* **SafetyContentFilter**: imitation learning "will happily learn bad habits
  along with good ones", so unsafe/destructive actions must be filtered *before*
  anything reaches the policy. Flags clips whose action labels match an
  unsafe-action blocklist.
* **BiasFilter**: web/egocentric video skews toward certain
  demographics/environments/tasks. Rebalances the dataset by capping the share
  of any single (source, task-family) stratum so no bucket dominates training.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..types import ClipRecord

# actions we never want a manipulation policy to imitate
_UNSAFE_KEYWORDS = {
    "throw", "smash", "break", "hit", "cut person", "burn", "stab",
    "slam", "destroy", "punch",
}


@dataclass
class FilterResult:
    kept: list[ClipRecord] = field(default_factory=list)
    removed: dict[str, str] = field(default_factory=dict)   # clip_id -> reason


class SafetyContentFilter:
    def __init__(self, blocklist: set[str] | None = None):
        self.blocklist = {k.lower() for k in (blocklist or _UNSAFE_KEYWORDS)}

    def _is_unsafe(self, clip: ClipRecord) -> str | None:
        texts = [clip.language_label] + [a.label for a in clip.actions]
        for text in texts:
            low = text.lower()
            for kw in self.blocklist:
                if kw in low:
                    return f"unsafe_action:{kw}"
        return None

    def filter(self, clips: list[ClipRecord]) -> FilterResult:
        res = FilterResult()
        for clip in clips:
            reason = self._is_unsafe(clip)
            if reason:
                res.removed[clip.clip_id] = reason
            else:
                res.kept.append(clip)
        return res


class BiasFilter:
    """Caps any (source_kind, task-family) stratum's share of the dataset."""

    def __init__(self, max_stratum_share: float = 0.5):
        self.max_stratum_share = max_stratum_share

    @staticmethod
    def _stratum(clip: ClipRecord) -> str:
        family = clip.language_label.split()[0] if clip.language_label else "unknown"
        return f"{clip.provenance.source_kind.value}:{family}"

    def filter(self, clips: list[ClipRecord]) -> FilterResult:
        res = FilterResult()
        n = len(clips)
        if n == 0:
            return res
        cap = max(1, int(self.max_stratum_share * n))
        counts: Counter[str] = Counter()
        for clip in clips:
            s = self._stratum(clip)
            if counts[s] < cap:
                counts[s] += 1
                res.kept.append(clip)
            else:
                res.removed[clip.clip_id] = f"stratum_capped:{s}"
        return res


def apply_dataset_filters(clips: list[ClipRecord], cfg) -> tuple[list[ClipRecord], dict]:
    """Run enabled filters in order (safety first, then bias). Returns (kept, report)."""
    report: dict = {}
    current = clips
    if getattr(cfg, "enable_safety_filter", True):
        r = SafetyContentFilter().filter(current)
        current, report["safety"] = r.kept, r.removed
    if getattr(cfg, "enable_bias_filter", True):
        r = BiasFilter().filter(current)
        current, report["bias"] = r.kept, r.removed
    return current, report
