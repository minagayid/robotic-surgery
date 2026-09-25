"""Robotic Surgery -- POV Video -> Robot Learning System.

A compliant, end-to-end pipeline for learning robot manipulation policies from
egocentric ("point-of-view") human video, implementing the six-layer design:

    1. Data acquisition (compliant sourcing)      -> robotic_surgery.learning_pipeline.data
    2. Ingestion & preprocessing                  -> robotic_surgery.learning_pipeline.preprocessing
    3. Human -> robot retargeting                 -> robotic_surgery.learning_pipeline.retargeting
    4. Learning architecture (representation+VLA) -> robotic_surgery.learning_pipeline.learning
    5. Sim-to-real validation & safety            -> robotic_surgery.learning_pipeline.sim2real
    6. Ops loop (versioning, filters, feedback)   -> robotic_surgery.learning_pipeline.ops

The model interfaces use deterministic mock backends by default. NumPy and
PyYAML are runtime dependencies; optional model packages are listed separately
in ``requirements-ml.txt``. Replacing a mock does not establish robot safety.
"""

from __future__ import annotations

from .config import PipelineConfig, load_config
from .pipeline import Pipeline
from .types import (
    ClipRecord,
    PseudoDemonstration,
    RobotAction,
    RobotDemonstration,
    VideoRef,
)

__version__ = "0.1.0"

__all__ = [
    "PipelineConfig",
    "load_config",
    "Pipeline",
    "ClipRecord",
    "PseudoDemonstration",
    "RobotAction",
    "RobotDemonstration",
    "VideoRef",
    "__version__",
]
