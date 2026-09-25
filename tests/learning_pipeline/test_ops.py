import numpy as np

from robotic_surgery.learning_pipeline.config import OpsConfig
from robotic_surgery.learning_pipeline.ops.feedback import FeedbackLoop
from robotic_surgery.learning_pipeline.ops.filters import BiasFilter, SafetyContentFilter, apply_dataset_filters
from robotic_surgery.learning_pipeline.ops.versioning import DatasetVersioner
from robotic_surgery.learning_pipeline.retargeting.representation import MockVisualEncoder
from robotic_surgery.learning_pipeline.sim2real.rollout import RolloutLog
from robotic_surgery.learning_pipeline.types import RobotDemonstration


def test_safety_filter_removes_unsafe(clips):
    clips[0].language_label = "smash the plate"
    res = SafetyContentFilter().filter(clips)
    assert clips[0].clip_id in res.removed
    assert "unsafe_action" in res.removed[clips[0].clip_id]


def test_bias_filter_caps_stratum(clips):
    # collapse every clip into one (source_kind, task-family) stratum; the cap
    # must then drop the surplus so no single bucket dominates training
    from robotic_surgery.learning_pipeline.types import SourceKind

    for c in clips:
        c.language_label = "pick cup"
        c.provenance.source_kind = SourceKind.RESEARCH_DATASET
    res = BiasFilter(max_stratum_share=0.5).filter(clips)
    assert len(res.kept) <= max(1, int(0.5 * len(clips)))
    assert len(res.removed) >= 1


def test_apply_dataset_filters(clips):
    kept, report = apply_dataset_filters(clips, OpsConfig())
    assert "safety" in report and "bias" in report
    assert len(kept) <= len(clips)


def test_versioner_dedup_and_commit(clips):
    enc = MockVisualEncoder()
    versioner = DatasetVersioner(enc, OpsConfig(dedup_threshold=0.999))
    stats = versioner.commit(clips)
    assert "added" in stats
    assert versioner.manifest.version == stats["version"]


def test_near_dedup_collapses_identical(clips):
    enc = MockVisualEncoder()
    versioner = DatasetVersioner(enc, OpsConfig(dedup_threshold=0.99))
    doubled = clips + clips  # exact duplicates by embedding
    kept, result = versioner.near_dedup(doubled)
    assert len(kept) <= len(clips)
    assert len(result.dropped) >= len(clips)


def test_feedback_prioritises_failures():
    logs = [
        RolloutLog(instruction="pour water", success=False),
        RolloutLog(instruction="pick up cup", success=True),
    ]
    demos = [RobotDemonstration("e0", [], [], "pick up cup", success=True)]
    fb = FeedbackLoop().ingest(logs, demos)
    assert fb.num_failure == 1
    assert fb.num_success == 1
    assert fb.priorities()[0][0] == "pour water"
    assert len(fb.new_finetune_demos) == 1
