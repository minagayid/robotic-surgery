import numpy as np

from robotic_surgery.learning_pipeline.config import PipelineConfig
from robotic_surgery.learning_pipeline.data.sources import FirstPartyCaptureSource, ResearchDatasetSource
from robotic_surgery.learning_pipeline.pipeline import Pipeline
from robotic_surgery.learning_pipeline.types import RobotAction, RobotDemonstration


def _sources():
    return [ResearchDatasetSource("ego4d", "d"), FirstPartyCaptureSource("captures")]


def test_pipeline_runs_end_to_end():
    cfg = PipelineConfig()
    report = Pipeline(cfg).run(_sources(), per_source_limit=2, validation_episodes=4)
    stages = report.summary()
    for key in ["ingest", "curate", "representation_pretrain", "retarget",
                "vla", "planner", "sim_validation", "rollout", "feedback"]:
        assert key in stages, f"missing stage {key}"
    assert stages["ingest"]["clips"] >= 1
    assert 0.0 <= stages["sim_validation"]["success_rate"] <= 1.0


def test_pipeline_with_robot_demos():
    cfg = PipelineConfig()
    pipe = Pipeline(cfg)
    # a real teleop demo folded into fine-tuning
    obs_source = list(ResearchDatasetSource("ego4d", "d").fetch(limit=1))
    clips = pipe.ingest([ResearchDatasetSource("ego4d", "d")], per_source_limit=1)
    demo = RobotDemonstration(
        "ep0", [clips[0].frames], [RobotAction(np.eye(4), 0.0)], "pick up cup", True
    )
    report = pipe.run(_sources(), per_source_limit=1, robot_demos=[demo],
                      validation_episodes=3)
    assert report["vla"]["finetune_transitions"] == 1


def test_pipeline_curation_enforces_license():
    cfg = PipelineConfig()
    pipe = Pipeline(cfg)
    clips = pipe.ingest([FirstPartyCaptureSource("captures")], per_source_limit=2)
    kept, report = pipe.curate(clips)
    assert "license" in report and "dataset" in report
    assert report["dataset"]["version"] >= 1
