"""Versioned calibration manifests and fail-closed admission checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class CalibrationManifest:
    calibration_id: str
    robot_model: str
    joint_count: int
    coordinate_frames: tuple[str, ...]
    created_at_ns: int
    expires_at_ns: int
    source: str
    checksum: str

    def __post_init__(self) -> None:
        if not self.calibration_id.strip() or not self.robot_model.strip() or not self.source.strip():
            raise ValueError("calibration identifiers and source must be non-empty")
        if self.joint_count < 1 or len(self.coordinate_frames) != self.joint_count:
            raise ValueError("calibration joint/frame dimensions are invalid")
        if any(not frame.strip() for frame in self.coordinate_frames):
            raise ValueError("coordinate frame names must be non-empty")
        if self.created_at_ns < 0 or self.expires_at_ns <= self.created_at_ns:
            raise ValueError("calibration timestamps are invalid")
        if len(self.checksum) != 64 or any(char not in "0123456789abcdef" for char in self.checksum.lower()):
            raise ValueError("calibration checksum must be a SHA-256 hex digest")

    @classmethod
    def create(
        cls,
        *,
        calibration_id: str,
        robot_model: str,
        joint_count: int,
        coordinate_frames: Iterable[str],
        created_at_ns: int,
        expires_at_ns: int,
        source: str,
    ) -> "CalibrationManifest":
        frames = tuple(coordinate_frames)
        payload = {
            "calibration_id": calibration_id,
            "robot_model": robot_model,
            "joint_count": joint_count,
            "created_at_ns": created_at_ns,
            "expires_at_ns": expires_at_ns,
            "source": source,
        }
        canonical = {**payload, "coordinate_frames": list(frames)}
        checksum = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return cls(checksum=checksum, coordinate_frames=frames, **payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibration_id": self.calibration_id,
            "robot_model": self.robot_model,
            "joint_count": self.joint_count,
            "coordinate_frames": list(self.coordinate_frames),
            "created_at_ns": self.created_at_ns,
            "expires_at_ns": self.expires_at_ns,
            "source": self.source,
            "checksum": self.checksum,
        }

    def compatible(self, *, calibration_id: str, joint_count: int, now_ns: int) -> bool:
        return (
            self.calibration_id == calibration_id
            and self.joint_count == joint_count
            and self.created_at_ns <= now_ns < self.expires_at_ns
        )


class CalibrationRegistry:
    """In-memory registry suitable for deterministic SIL/HIL fixtures."""

    def __init__(self, manifests: Iterable[CalibrationManifest] = ()) -> None:
        self._manifests: dict[str, CalibrationManifest] = {}
        for manifest in manifests:
            self.register(manifest)

    def register(self, manifest: CalibrationManifest) -> None:
        existing = self._manifests.get(manifest.calibration_id)
        if existing is not None and existing.checksum != manifest.checksum:
            raise ValueError("calibration id already registered with a different checksum")
        self._manifests[manifest.calibration_id] = manifest

    def get(self, calibration_id: str) -> CalibrationManifest | None:
        return self._manifests.get(calibration_id)

    def require(self, calibration_id: str, *, joint_count: int, now_ns: int) -> CalibrationManifest:
        manifest = self.get(calibration_id)
        if manifest is None:
            raise ValueError("calibration manifest is not registered")
        if not manifest.compatible(calibration_id=calibration_id, joint_count=joint_count, now_ns=now_ns):
            raise ValueError("calibration manifest is incompatible or expired")
        return manifest

    def to_dict(self) -> dict[str, dict[str, Any]]:
        return {key: value.to_dict() for key, value in sorted(self._manifests.items())}
