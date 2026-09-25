"""Append-only local event journal with a tamper-evident hash chain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


class EventJournal:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "0" * 64
        last = "0" * 64
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                last = json.loads(line)["hash"]
        return last

    def append(self, payload: dict[str, Any]) -> str:
        previous = self._last_hash()
        record = {"prev_hash": previous, "payload": payload}
        digest = hashlib.sha256(_canonical(record)).hexdigest()
        record["hash"] = digest
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
        return digest

    def verify(self) -> bool:
        if not self.path.exists():
            return True
        previous = "0" * 64
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("prev_hash") != previous:
                    return False
                stored = record.get("hash")
                unsigned = {"prev_hash": record["prev_hash"], "payload": record["payload"]}
                expected = hashlib.sha256(_canonical(unsigned)).hexdigest()
                if stored != expected:
                    return False
                previous = stored
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False
        return True

    def replay(self) -> list[dict[str, Any]]:
        if not self.verify():
            raise ValueError("event journal integrity check failed")
        if not self.path.exists():
            return []
        return [json.loads(line)["payload"] for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
