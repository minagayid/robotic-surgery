from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from robotic_os.data import OfflineDatasetManifest, OfflineDatasetRegistry


class OfflineDatasetRegistryTests(unittest.TestCase):
    def manifest(self, **overrides):
        values = {
            "dataset_id": "example-clinical-pov",
            "version": "2026-01",
            "source_url": "https://provider.example/datasets/example",
            "sha256": "a" * 64,
            "license_name": "Research license",
            "ethics_basis": "Provider IRB/de-identification statement reviewed by the data custodian",
            "clinical_status": "clinical_endoscopic",
            "deidentified": True,
            "split_key": "procedure_id",
            "permitted_uses": ("representation", "perception"),
        }
        values.update(overrides)
        return OfflineDatasetManifest(**values)

    def test_research_perception_use_is_admitted_after_provenance_checks(self) -> None:
        payload = b"approved-offline-dataset-fixture"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dataset.bin"
            path.write_bytes(payload)
            registry = OfflineDatasetRegistry()
            registry.register(
                self.manifest(sha256=hashlib.sha256(payload).hexdigest())
            )
            decision = registry.admit(
                "example-clinical-pov",
                intended_use="perception",
                archive_path=path,
            )
            self.assertEqual(decision.status, "admitted_for_research")

    def test_direct_actuation_use_is_rejected(self) -> None:
        registry = OfflineDatasetRegistry()
        registry.register(self.manifest())
        decision = registry.admit("example-clinical-pov", intended_use="direct_actuation")
        self.assertEqual(decision.status, "rejected")
        self.assertIn("clinical_data_cannot_authorize_direct_actuation", decision.reasons)

    def test_archive_checksum_is_verified(self) -> None:
        payload = b"offline-dataset-archive-fixture"
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dataset.bin"
            path.write_bytes(payload)
            self.assertTrue(OfflineDatasetRegistry.verify_archive(path, digest))
            self.assertFalse(OfflineDatasetRegistry.verify_archive(path, "b" * 64))

    def test_non_deidentified_manifest_is_rejected(self) -> None:
        registry = OfflineDatasetRegistry()
        registry.register(self.manifest(deidentified=False))
        decision = registry.admit(
            "example-clinical-pov",
            intended_use="perception",
            archive_path=Path("missing.bin"),
        )
        self.assertEqual(decision.status, "rejected")
        self.assertIn("deidentification_evidence_required", decision.reasons)

    def test_admission_requires_archive_verification(self) -> None:
        registry = OfflineDatasetRegistry()
        registry.register(self.manifest())
        decision = registry.admit("example-clinical-pov", intended_use="perception")
        self.assertEqual(decision.status, "rejected")
        self.assertIn("archive_not_verified", decision.reasons)


if __name__ == "__main__":
    unittest.main()
