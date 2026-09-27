"""Layer 6 -- the ops loop (Section 6).

    Video sources -> curated dataset -> representation pretraining
          |                                    |
      dataset versioning                robot fine-tuning
      (dedup, bias/safety filter)              |
          ^                            real-world rollout
          +--------- failure cases feed back ---+

* :mod:`~robotx.ops.versioning` -- embedding dedup + manifest versioning.
* :mod:`~robotx.ops.filters`     -- bias and action-safety dataset filters.
* :mod:`~robotx.ops.feedback`    -- fold rollout failures back into the dataset.
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
