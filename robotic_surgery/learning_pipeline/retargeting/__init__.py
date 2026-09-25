"""Mock representation and retargeting interfaces for offline pipeline tests.

The fixed mock encoder and mock hand trajectories are not learned features or
measured human motion. Pseudo-demonstrations produced from them must not be
treated as robot actions, control data, or performance evidence.
"""

from .kinematic import KinematicRetargeter
from .representation import EncoderBackend, VisualEncoder, build_encoder

__all__ = [
    "KinematicRetargeter",
    "VisualEncoder",
    "EncoderBackend",
    "build_encoder",
]
