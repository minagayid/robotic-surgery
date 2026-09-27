"""robotX -- POV Video -> Robot Learning System.

A compliant, end-to-end pipeline for learning robot manipulation policies from
egocentric ("point-of-view") human video, implementing the six-layer design:

    1. Data acquisition (compliant sourcing)      -> robotx.data
    2. Ingestion & preprocessing                  -> robotx.preprocessing
    3. Human -> robot retargeting                 -> robotx.retargeting
    4. Learning architecture (representation+VLA) -> robotx.learning
    5. Sim-to-real validation & safety            -> robotx.sim2real
    6. Ops loop (versioning, filters, feedback)   -> robotx.ops

The pipeline runs end-to-end on dependency-free mock backends (see
``robotx.config.BackendConfig``); swap in real models via requirements-ml.txt.
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
