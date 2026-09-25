import numpy as np

from robotic_surgery.learning_pipeline.data.licensing import LicenseGate
from robotic_surgery.learning_pipeline.data.manifest import DatasetManifest, content_hash
from robotic_surgery.learning_pipeline.data.sources import (
    FirstPartyCaptureSource,
    LicensedPartnerSource,
    OfficialAPISource,
    ResearchDatasetSource,
    build_source,
)
from robotic_surgery.learning_pipeline.types import LicenseStatus, SourceKind


def test_sources_stamp_provenance():
    api = OfficialAPISource("youtube", "cooking")
    refs = list(api.fetch(limit=3))
    assert len(refs) == 3
    assert all(r.provenance.source_kind == SourceKind.OFFICIAL_API for r in refs)
    assert all(r.provenance.license_status == LicenseStatus.RESEARCH_ONLY for r in refs)


def test_first_party_and_licensed_are_cleared():
    fp = list(FirstPartyCaptureSource("captures").fetch(limit=2))
    lp = list(LicensedPartnerSource("acme", "lic-1").fetch(limit=2))
    assert all(r.provenance.trainable for r in fp + lp)
    assert all(r.provenance.license_status == LicenseStatus.CLEARED for r in fp + lp)


def test_unknown_dataset_rejected():
    import pytest

    with pytest.raises(ValueError):
        ResearchDatasetSource("not_a_dataset", "x")


def test_build_source_factory():
    src = build_source({"type": "research", "name": "epic_kitchens"})
    assert isinstance(src, ResearchDatasetSource)


def test_license_gate_blocks_pending(clips):
    # force one clip to PENDING and confirm it is filtered out
    clips[0].provenance.license_status = LicenseStatus.PENDING
    kept, result = LicenseGate().filter(clips)
    assert clips[0].clip_id in result.rejected
    assert clips[0].clip_id not in {c.clip_id for c in kept}


def test_manifest_dedup(clips):
    m = DatasetManifest()
    first = m.add_many(clips)
    assert first["added"] == len(clips)
    # re-adding identical clips -> all duplicates, version unchanged
    v = m.version
    again = m.add_many(clips)
    assert again["added"] == 0
    assert again["duplicates"] == len(clips)
    assert m.version == v


def test_manifest_roundtrip(tmp_path, clips):
    m = DatasetManifest()
    m.add_many(clips)
    p = tmp_path / "manifest.json"
    m.save(p)
    loaded = DatasetManifest.load(p)
    assert loaded.version == m.version
    assert loaded.clip_ids == m.clip_ids


def test_content_hash_stable(clips):
    assert content_hash(clips[0]) == content_hash(clips[0])
