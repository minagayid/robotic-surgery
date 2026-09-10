"""Versioned, portable telemetry records for local replay and data ingest."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TELEMETRY_SCHEMA_VERSION = 1
MAX_PAYLOAD_BYTES = 256_000


@dataclass(frozen=True)
class TelemetryRecord:
    event_type: str
    timestamp_ns: int
    source_id: str
    calibration_id: str
    safety_status: str
    payload: dict[str, Any]
    record_id: str = ""
    schema_version: int = TELEMETRY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TELEMETRY_SCHEMA_VERSION:
            raise ValueError("unsupported telemetry schema")
        if not self.event_type or not self.source_id or not self.calibration_id:
            raise ValueError("telemetry identity is required")
        if self.timestamp_ns < 0 or not isinstance(self.payload, dict):
            raise ValueError("telemetry timestamp or payload is invalid")
        encoded = json.dumps(self.payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_PAYLOAD_BYTES:
            raise ValueError("telemetry payload exceeds the bounded record size")
        if not self.record_id:
            object.__setattr__(self, "record_id", uuid.uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "event_type": self.event_type,
            "timestamp_ns": self.timestamp_ns,
            "source_id": self.source_id,
            "calibration_id": self.calibration_id,
            "safety_status": self.safety_status,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TelemetryRecord":
        return cls(
            event_type=str(data["event_type"]),
            timestamp_ns=int(data["timestamp_ns"]),
            source_id=str(data["source_id"]),
            calibration_id=str(data["calibration_id"]),
            safety_status=str(data.get("safety_status", "unknown")),
            payload=dict(data.get("payload", {})),
            record_id=str(data.get("record_id", "")),
            schema_version=int(data.get("schema_version", 0)),
        )


def append_jsonl(path: str | Path, record: TelemetryRecord) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False, separators=(",", ":")) + "\n")


def read_jsonl(path: str | Path) -> tuple[TelemetryRecord, ...]:
    target = Path(path)
    if not target.exists():
        return ()
    records = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(TelemetryRecord.from_dict(json.loads(line)))
    return tuple(records)
