from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from robotic_surgery.events import EventJournal


class EventJournalTests(unittest.TestCase):
    def test_hash_chain_verifies_and_replays(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal = EventJournal(Path(temp_dir) / "events.jsonl")
            journal.append({"type": "boot", "timestamp_ns": 1})
            journal.append({"type": "decision", "status": "approved", "timestamp_ns": 2})
            self.assertTrue(journal.verify())
            self.assertEqual([item["type"] for item in journal.replay()], ["boot", "decision"])

    def test_tampering_breaks_hash_chain_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            journal = EventJournal(path)
            journal.append({"type": "boot", "timestamp_ns": 1})
            record = json.loads(path.read_text(encoding="utf-8"))
            record["payload"]["type"] = "tampered"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            self.assertFalse(journal.verify())


if __name__ == "__main__":
    unittest.main()
