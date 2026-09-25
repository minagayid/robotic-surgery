"""Reproducible local dataset manifests with exact content deduplication."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..types import ClipRecord, to_jsonable


_MANIFEST_SCHEMA_VERSION = 1


def content_hash(clip: ClipRecord) -> str:
    """Return a stable digest for a clip's immutable source and extracted content."""

    digest = hashlib.sha256()
    digest.update(clip.clip_id.encode("utf-8"))
    digest.update(clip.provenance.source_kind.value.encode("utf-8"))
    digest.update(clip.provenance.source_id.encode("utf-8"))
    digest.update(clip.provenance.license_status.value.encode("utf-8"))
    frames = np.ascontiguousarray(clip.frames.frames)
    digest.update(str(frames.shape).encode("ascii"))
    digest.update(frames.tobytes())
    digest.update(json.dumps(to_jsonable(clip.metadata), sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


@dataclass
class DatasetManifest:
    """Stores exact clip hashes and summaries, never full raw media."""

    version: int = 0
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def clip_ids(self) -> list[str]:
        return sorted(entry["clip_id"] for entry in self.entries.values())

    def add_many(self, clips: list[ClipRecord]) -> dict[str, int]:
        added = 0
        duplicates = 0
        for clip in clips:
            digest = content_hash(clip)
            if digest in self.entries:
                duplicates += 1
                continue
            self.entries[digest] = {"clip_id": clip.clip_id, "summary": to_jsonable(clip.summary())}
            added += 1
        if added:
            self.version += 1
        return {"added": added, "duplicates": duplicates, "version": self.version}

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": _MANIFEST_SCHEMA_VERSION,
            "version": self.version,
            "entries": self.entries,
        }
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "DatasetManifest":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != _MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported manifest schema version")
        entries = payload.get("entries")
        if not isinstance(entries, dict):
            raise ValueError("manifest entries must be an object")
        return cls(version=int(payload.get("version", 0)), entries=entries)
