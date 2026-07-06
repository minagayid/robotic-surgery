"""Layer 3 -- human -> robot retargeting (the core embodiment gap).

Human video contains no robot actions. Two complementary approaches, both here:

* **A. Representation learning** (:mod:`~robotx.retargeting.representation`) --
  a self-supervised visual encoder (R3M / VIP / VC-1 style) trained on the human
  video so the robot's vision backbone understands grasping, pouring, etc. No
  retargeting needed; the policy later needs far fewer robot demos.

* **B. Kinematic retargeting** (:mod:`~robotx.retargeting.kinematic`) -- map the
  estimated human wrist/finger trajectory onto the robot end-effector to produce
  a *pseudo-demonstration*. Inherently noisy -> weak supervision only.
"""

from .kinematic import KinematicRetargeter
from .representation import EncoderBackend, VisualEncoder, build_encoder

__all__ = [
    "KinematicRetargeter",
    "VisualEncoder",
    "EncoderBackend",
    "build_encoder",
]
