"""Layer 6 -- the ops loop (Section 6).

    Video sources -> curated dataset -> representation pretraining
          |                                    |
      dataset versioning                robot fine-tuning
      (dedup, bias/safety filter)              |
          ^                            real-world rollout
          +--------- failure cases feed back ---+

* :mod:`~robotic_surgery.learning_pipeline.ops.versioning` -- embedding dedup + manifest versioning.
* :mod:`~robotic_surgery.learning_pipeline.ops.filters`     -- bias and action-safety dataset filters.
* :mod:`~robotic_surgery.learning_pipeline.ops.feedback`    -- fold rollout failures back into the dataset.
"""

from .feedback import FeedbackLoop, FeedbackResult
from .filters import BiasFilter, SafetyContentFilter, apply_dataset_filters
from .versioning import DatasetVersioner, DedupResult

__all__ = [
    "DatasetVersioner",
    "DedupResult",
    "BiasFilter",
    "SafetyContentFilter",
    "apply_dataset_filters",
    "FeedbackLoop",
    "FeedbackResult",
]
