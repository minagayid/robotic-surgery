"""Compliant video-source adapters.

These adapters deliberately return deterministic *references*, not downloaded media.
They make the local mock pipeline runnable while keeping the boundary explicit: a
production integration must call an authorised provider API or read a user-owned
capture directory and preserve the resulting provenance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..types import LicenseStatus, Provenance, SourceKind, VideoRef

_RESEARCH_DATASETS = {
    "ego4d": "Ego4D",
    "ego_exo4d": "Ego-Exo4D",
    "epic_kitchens": "EPIC-KITCHENS",
    "ssv2": "Something-Something-V2",
    "howto100m": "HowTo100M",
    "yt8m": "YouTube-8M",
}
_ALLOWED_PLATFORMS = {"youtube", "x", "meta", "tiktok"}


@dataclass
class VideoSource(ABC):
    """A source that yields provenance-stamped video references."""

    @abstractmethod
    def fetch(self, limit: int | None = None) -> Iterator[VideoRef]:
        """Yield no more than ``limit`` deterministic references."""


def _limit(limit: int | None) -> range:
    if limit is None:
        limit = 1
    if limit < 0:
        raise ValueError("limit must be non-negative")
    return range(limit)


def _ref(
    *,
    uri: str,
    source_kind: SourceKind,
    source_id: str,
    status: LicenseStatus,
    attribution: str | None = None,
    consent_ref: str | None = None,
    seed: int = 0,
    metadata: dict[str, Any] | None = None,
) -> VideoRef:
    return VideoRef(
        uri=uri,
        provenance=Provenance(
            source_kind=source_kind,
            source_id=source_id,
            license_status=status,
            attribution=attribution,
            consent_ref=consent_ref,
        ),
        fps=30.0,
        duration_s=2.0,
        width=320,
        height=240,
        metadata={"seed": seed, "mock": True, **(metadata or {})},
    )


@dataclass
class OfficialAPISource(VideoSource):
    """A placeholder for an authorised official-platform API integration.

    The local implementation performs no network request and never claims that
    a returned reference is cleared for commercial training.
    """

    platform: str
    query: str

    def __post_init__(self) -> None:
        self.platform = self.platform.lower()
        if self.platform not in _ALLOWED_PLATFORMS:
            raise ValueError(f"unsupported official platform: {self.platform}")
        if not self.query.strip():
            raise ValueError("query must not be empty")

    def fetch(self, limit: int | None = None) -> Iterator[VideoRef]:
        for index in _limit(limit):
            source_id = f"{self.platform}:{self.query}:{index}"
            yield _ref(
                uri=f"official-api://{self.platform}/{self.query}/{index}",
                source_kind=SourceKind.OFFICIAL_API,
                source_id=source_id,
                status=LicenseStatus.RESEARCH_ONLY,
                attribution=f"{self.platform} official API query: {self.query}",
                seed=index,
                metadata={"platform": self.platform, "query": self.query},
            )


@dataclass
class ResearchDatasetSource(VideoSource):
    """Reference adapter for pre-licensed research datasets in local storage."""

    name: str
    root: str

    def __post_init__(self) -> None:
        self.name = self.name.lower()
        if self.name not in _RESEARCH_DATASETS:
            supported = ", ".join(sorted(_RESEARCH_DATASETS))
            raise ValueError(f"unknown research dataset: {self.name}; supported: {supported}")
        if not self.root:
            raise ValueError("root must not be empty")

    def fetch(self, limit: int | None = None) -> Iterator[VideoRef]:
        for index in _limit(limit):
            source_id = f"{self.name}:mock-{index:05d}"
            yield _ref(
                uri=str(Path(self.root) / self.name / f"mock-{index:05d}.mp4"),
                source_kind=SourceKind.RESEARCH_DATASET,
                source_id=source_id,
                status=LicenseStatus.RESEARCH_ONLY,
                attribution=_RESEARCH_DATASETS[self.name],
                seed=index,
                metadata={"dataset": self.name, "root": self.root},
            )


@dataclass
class LicensedPartnerSource(VideoSource):
    """Reference adapter for creator material covered by an explicit license."""

    partner: str
    license_ref: str

    def __post_init__(self) -> None:
        if not self.partner.strip() or not self.license_ref.strip():
            raise ValueError("partner and license_ref must not be empty")

    def fetch(self, limit: int | None = None) -> Iterator[VideoRef]:
        for index in _limit(limit):
            source_id = f"{self.partner}:licensed-{index:05d}"
            yield _ref(
                uri=f"licensed://{self.partner}/clip-{index:05d}.mp4",
                source_kind=SourceKind.LICENSED_PARTNER,
                source_id=source_id,
                status=LicenseStatus.CLEARED,
                attribution=self.partner,
                consent_ref=self.license_ref,
                seed=index,
                metadata={"partner": self.partner, "license_ref": self.license_ref},
            )


@dataclass
class FirstPartyCaptureSource(VideoSource):
    """Reference adapter for locally owned, consented first-party captures."""

    capture_dir: str
    consent_ref: str = "first-party-capture-consent"

    def __post_init__(self) -> None:
        if not self.capture_dir:
            raise ValueError("capture_dir must not be empty")

    def fetch(self, limit: int | None = None) -> Iterator[VideoRef]:
        for index in _limit(limit):
            source_id = f"first-party:{Path(self.capture_dir).name or 'capture'}:{index:05d}"
            yield _ref(
                uri=str(Path(self.capture_dir) / f"capture-{index:05d}.mp4"),
                source_kind=SourceKind.FIRST_PARTY,
                source_id=source_id,
                status=LicenseStatus.CLEARED,
                attribution="first-party capture",
                consent_ref=self.consent_ref,
                seed=index,
                metadata={"capture_dir": self.capture_dir},
            )


def build_source(spec: dict[str, Any]) -> VideoSource:
    """Build a sanctioned source from a concise, serialisable configuration."""

    source_type = str(spec.get("type", "")).lower()
    if source_type == "official_api":
        return OfficialAPISource(str(spec["platform"]), str(spec["query"]))
    if source_type == "research":
        return ResearchDatasetSource(str(spec["name"]), str(spec.get("root", "datasets")))
    if source_type == "licensed":
        return LicensedPartnerSource(str(spec["partner"]), str(spec["license_ref"]))
    if source_type == "first_party":
        return FirstPartyCaptureSource(str(spec.get("capture_dir", "captures")), str(spec.get("consent_ref", "first-party-capture-consent")))
    raise ValueError(f"unsupported source type: {source_type or '<missing>'}")


def collect(sources: Sequence[VideoSource], per_source_limit: int | None = None) -> list[VideoRef]:
    """Collect only source references, preserving input order and provenance."""

    refs: list[VideoRef] = []
    for source in sources:
        refs.extend(source.fetch(limit=per_source_limit))
    return refs
