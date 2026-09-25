import numpy as np
import pytest

from robotic_surgery.learning_pipeline.config import PipelineConfig
from robotic_surgery.learning_pipeline.data.sources import FirstPartyCaptureSource, ResearchDatasetSource
from robotic_surgery.learning_pipeline.preprocessing.clip_builder import ClipBuilder


@pytest.fixture
def cfg() -> PipelineConfig:
    c = PipelineConfig()
    c.seed = 7
    return c


@pytest.fixture
def sources():
    return [
        ResearchDatasetSource("ego4d", "datasets"),
        FirstPartyCaptureSource("captures"),
    ]


@pytest.fixture
def clips(cfg, sources):
    builder = ClipBuilder(cfg)
    out = []
    for src in sources:
        for ref in src.fetch(limit=2):
            built, _ = builder.build(ref)
            out.extend(built)
    return out
