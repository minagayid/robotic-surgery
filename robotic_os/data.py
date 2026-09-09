"""Offline dataset provenance and training-use admission controls.

This module does not download, de-identify, or approve clinical data. It makes
the evidence required before a locally cached archive can enter a research
training workflow explicit and reproducible.
"""

from __future__ import annotations

import hashlib
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


CLINICAL_STATUSES = frozenset({"clinical_endoscopic", "clinical_or", "phantom", "ex_vivo", "synthetic", "mixed"})
TRAINING_USES = frozenset({"representation", "perception", "spatial_mapping", "skill_assessment", "simulation"})
FORBIDDEN_USES = frozenset({"direct_actuation", "autonomous_clinical_execution"})
SPLIT_KEYS = frozenset({"patient_id", "procedure_id", "session_id", "surgeon_id", "site_id"})
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class OfflineDatasetManifest:
    """Minimum provenance needed to admit one immutable offline archive."""

    dataset_id: str
    version: str
    source_url: str
    sha256: str
    license_name: str
    ethics_basis: str
    clinical_status: str
    deidentified: bool
    split_key: str
    permitted_uses: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, name, limit in (
            (self.dataset_id, "dataset_id", 160),
            (self.version, "version", 80),
            (self.license_name, "license_name", 200),
            (self.ethics_basis, "ethics_basis", 500),
        ):
            if not value or len(value) > limit or not value.strip():
                raise ValueError(f"{name} must be a non-empty bounded identifier")
        parsed = urllib.parse.urlparse(self.source_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("source_url must be an HTTPS provider URL")
        if not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")
        if self.clinical_status not in CLINICAL_STATUSES:
            raise ValueError("clinical_status is invalid")
        if not isinstance(self.deidentified, bool):
            raise ValueError("deidentified must be a boolean")
        if self.split_key not in SPLIT_KEYS:
            raise ValueError("split_key must prevent leakage across a named unit")
        uses = tuple(dict.fromkeys(str(use) for use in self.permitted_uses))
        if not uses or any(use not in TRAINING_USES for use in uses):
            raise ValueError("permitted_uses contains an unsupported or empty use")
        object.__setattr__(self, "permitted_uses", uses)

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "source_url": self.source_url,
            "sha256": self.sha256.lower(),
            "license_name": self.license_name,
            "ethics_basis": self.ethics_basis,
            "clinical_status": self.clinical_status,
            "deidentified": self.deidentified,
            "split_key": self.split_key,
            "permitted_uses": list(self.permitted_uses),
        }


@dataclass(frozen=True)
class DatasetAdmissionDecision:
    dataset_id: str
    intended_use: str
    status: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "intended_use": self.intended_use,
            "status": self.status,
            "reasons": list(self.reasons),
        }


class OfflineDatasetRegistry:
    """Registry that keeps offline data usable for research, never actuation."""

    def __init__(self) -> None:
        self._manifests: dict[str, OfflineDatasetManifest] = {}

    @property
    def manifests(self) -> tuple[OfflineDatasetManifest, ...]:
        return tuple(self._manifests.values())

    def register(self, manifest: OfflineDatasetManifest) -> None:
        if manifest.dataset_id in self._manifests:
            raise ValueError("dataset_id is already registered")
        self._manifests[manifest.dataset_id] = manifest

    def admit(
        self,
        dataset_id: str,
        *,
        intended_use: str,
        archive_path: Path | str | None = None,
    ) -> DatasetAdmissionDecision:
        """Admit a locally cached archive for a bounded research use.

        A manifest is provenance metadata, not evidence that the bytes on
        disk are the bytes that were reviewed.  Admission therefore requires
        a checksum match.  Direct actuation and autonomous clinical
        execution are rejected regardless of the labels or archive.
        """
        manifest = self._manifests.get(dataset_id)
        if manifest is None:
            return DatasetAdmissionDecision(dataset_id, intended_use, "rejected", ("dataset_not_registered",))
        reasons: list[str] = []
        if intended_use in FORBIDDEN_USES:
            reasons.append("clinical_data_cannot_authorize_direct_actuation")
        if intended_use not in manifest.permitted_uses:
            reasons.append("intended_use_not_permitted_by_manifest")
        if not manifest.deidentified:
            reasons.append("deidentification_evidence_required")
        if archive_path is None:
            reasons.append("archive_not_verified")
        elif not self.verify_archive(archive_path, manifest.sha256):
            reasons.append("archive_checksum_mismatch")
        if reasons:
            return DatasetAdmissionDecision(dataset_id, intended_use, "rejected", tuple(dict.fromkeys(reasons)))
        return DatasetAdmissionDecision(dataset_id, intended_use, "admitted_for_research", ())

    @staticmethod
    def verify_archive(path: Path | str, expected_sha256: str) -> bool:
        """Verify a locally cached archive without trusting its filename."""
        if not _SHA256.fullmatch(expected_sha256):
            raise ValueError("expected_sha256 must be a 64-character hexadecimal digest")
        archive = Path(path)
        if not archive.is_file():
            return False
        digest = hashlib.sha256()
        try:
            with archive.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError:
            return False
        return digest.hexdigest() == expected_sha256.lower()
