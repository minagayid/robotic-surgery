import sys
from pathlib import Path

# make src/ importable without an editable install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pytest

from robotx.config import PipelineConfig
from robotx.data.sources import FirstPartyCaptureSource, ResearchDatasetSource
from robotx.preprocessing.clip_builder import ClipBuilder


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
