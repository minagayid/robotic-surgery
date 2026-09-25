"""Compliant, local-first data acquisition and dataset manifest utilities."""

from .licensing import GateResult, LicenseGate
from .manifest import DatasetManifest, content_hash
from .sources import (
    FirstPartyCaptureSource,
    LicensedPartnerSource,
    OfficialAPISource,
    ResearchDatasetSource,
    VideoSource,
    build_source,
    collect,
)

__all__ = [
    "DatasetManifest",
    "FirstPartyCaptureSource",
    "GateResult",
    "LicenseGate",
    "LicensedPartnerSource",
    "OfficialAPISource",
    "ResearchDatasetSource",
    "VideoSource",
    "build_source",
    "collect",
    "content_hash",
]
