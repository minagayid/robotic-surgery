"""A single enforceable license checkpoint for training data."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..types import ClipRecord, LicenseStatus


@dataclass
class GateResult:
    allowed: list[str] = field(default_factory=list)
    rejected: dict[str, str] = field(default_factory=dict)

    @property
    def num_allowed(self) -> int:
        return len(self.allowed)


@dataclass
class LicenseGate:
    """Filter clips by the license status stamped in their provenance.

    Research-only material can be enabled for research workflows but remains
    excluded when ``allow_research_only`` is false. Pending and blocked sources
    never pass through this gate.
    """

    allow_research_only: bool = True

    def filter(self, clips: list[ClipRecord]) -> tuple[list[ClipRecord], GateResult]:
        kept: list[ClipRecord] = []
        result = GateResult()
        for clip in clips:
            status = clip.provenance.license_status
            if status is LicenseStatus.CLEARED:
                kept.append(clip)
                result.allowed.append(clip.clip_id)
            elif status is LicenseStatus.RESEARCH_ONLY and self.allow_research_only:
                kept.append(clip)
                result.allowed.append(clip.clip_id)
            else:
                result.rejected[clip.clip_id] = status.value
        return kept, result
