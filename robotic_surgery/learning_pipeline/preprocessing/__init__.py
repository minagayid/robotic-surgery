"""Layer 2 -- ingestion & preprocessing.

Pipeline (design doc Section 2)::

    Raw video -> shot segmentation -> frame sampling (2-8 fps)
              -> quality filter -> privacy filter
              -> per-clip extraction {hand pose, egomotion, tracks, depth,
                                       action segments, language label}
              -> ClipRecord

The interfaces currently have deterministic mock implementations so the whole
stage runs offline. Referenced real models are potential future integrations;
none is included or enabled by installing optional dependencies.
"""

from .clip_builder import ClipBuilder
from .extractors import (
    ActionSegmenter,
    DepthEstimator,
    EgoMotionEstimator,
    HandPoseEstimator,
    LanguageGrounder,
    ObjectTrackerDetector,
    build_extractors,
)
from .privacy import PrivacyRedactor
from .quality import QualityFilter
from .sampling import sample_frames
from .segmentation import segment_shots

__all__ = [
    "segment_shots",
    "sample_frames",
    "QualityFilter",
    "PrivacyRedactor",
    "HandPoseEstimator",
    "EgoMotionEstimator",
    "ObjectTrackerDetector",
    "DepthEstimator",
    "ActionSegmenter",
    "LanguageGrounder",
    "build_extractors",
    "ClipBuilder",
]
