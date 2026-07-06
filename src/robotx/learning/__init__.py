"""Layer 4 -- learning architecture.

Three components mirroring the design doc's diagram:

* :mod:`~robotx.learning.pretrain`   -- self-supervised representation
  pretraining on human video (feeds the policy's vision backbone).
* :mod:`~robotx.learning.vla_policy` -- a Vision-Language-Action policy
  (OpenVLA / Octo style) pretrained on human-video representations and
  fine-tuned on real robot teleop demos.
* :mod:`~robotx.learning.planner`    -- a high-level VLM/LLM planner that
  decomposes tasks and grounds instructions, run at a lower frequency than
  low-level control.
"""

from .planner import HighLevelPlanner, Plan
from .pretrain import RepresentationTrainer, PretrainResult
from .vla_policy import VLAPolicy, build_policy

__all__ = [
    "RepresentationTrainer",
    "PretrainResult",
    "VLAPolicy",
    "build_policy",
    "HighLevelPlanner",
    "Plan",
]
