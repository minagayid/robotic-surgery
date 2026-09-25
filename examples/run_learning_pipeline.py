"""Run the full Robotic Surgery pipeline end-to-end on mock backends.

    python examples/run_learning_pipeline.py

Demonstrates the realistic "research datasets for pretraining + first-party
capture for the target task" blend, plus a real robot teleop demo folded into
fine-tuning.
"""

from __future__ import annotations

import json

import numpy as np

from robotic_surgery.learning_pipeline import Pipeline, PipelineConfig
from robotic_surgery.learning_pipeline.data.sources import FirstPartyCaptureSource, ResearchDatasetSource
from robotic_surgery.learning_pipeline.types import RobotAction, RobotDemonstration


def main() -> None:
    cfg = PipelineConfig()
    cfg.seed = 42

    pipe = Pipeline(cfg)

    # broad pretraining data + targeted first-party capture
    sources = [
        ResearchDatasetSource("ego4d", "datasets"),
        ResearchDatasetSource("epic_kitchens", "datasets"),
        FirstPartyCaptureSource("captures/coffee_task"),
    ]

    # a single real teleop demonstration (ground truth) for fine-tuning
    clips = pipe.ingest([FirstPartyCaptureSource("captures/coffee_task")],
                        per_source_limit=1)
    teleop = RobotDemonstration(
        episode_id="teleop-0",
        observations=[clips[0].frames],
        actions=[RobotAction(ee_pose=np.eye(4), gripper=0.0)],
        language_instruction="pick up cup",
        success=True,
    )

    report = pipe.run(
        sources,
        per_source_limit=3,
        robot_demos=[teleop],
        eval_instruction="pick up cup",
        validation_episodes=8,
    )

    print(json.dumps(report.summary(), indent=2, default=str))


if __name__ == "__main__":
    main()
