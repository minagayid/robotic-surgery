"""Local hash-chained JSONL event journal and deterministic reader."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Iterator


GENESIS_HASH = "0" * 64


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(slots=True)
class EventJournal:
    path: Path
    sync_writes: bool = True
    _last_hash: str = field(init=False, default=GENESIS_HASH, repr=False)

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = GENESIS_HASH
        if self.path.exists() and self.path.stat().st_size:
            for record in read_verified_events(self.path):
                self._last_hash = record["record_hash"]

    def append(self, kind: str, monotonic_ns: int, payload: dict[str, Any]) -> str:
        if not kind:
            raise ValueError("event kind is required")
        unsigned = {
            "kind": kind,
            "monotonic_ns": monotonic_ns,
            "payload": payload,
            "previous_hash": self._last_hash,
            "schema_version": 1,
        }
        record_hash = sha256(_canonical_json(unsigned).encode("utf-8")).hexdigest()
        record = {**unsigned, "record_hash": record_hash}
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(_canonical_json(record) + "\n")
            stream.flush()
            if self.sync_writes:
                os.fsync(stream.fileno())
        self._last_hash = record_hash
        return record_hash


def read_verified_events(path: Path) -> Iterator[dict[str, Any]]:
    previous_hash = GENESIS_HASH
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            record = json.loads(line)
            actual_hash = record.pop("record_hash", None)
            expected_hash = sha256(_canonical_json(record).encode("utf-8")).hexdigest()
            if record.get("previous_hash") != previous_hash or actual_hash != expected_hash:
                raise ValueError(f"event journal integrity failure at line {line_number}")
            record["record_hash"] = actual_hash
            previous_hash = actual_hash
            yield record
