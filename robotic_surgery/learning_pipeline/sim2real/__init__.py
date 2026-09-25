"""Toy simulation validation, command bounds, and simulation logs only.

There is no robot hardware driver, deployment gate, or physical safety case in
this package. Simulation success alone must never be used to authorize hardware.
"""

from .rollout import RolloutLog, StagedRollout
from .safety import SafetyEnvelope, SafetyViolation
from .validation import SimValidator, ValidationReport

__all__ = [
    "SafetyEnvelope",
    "SafetyViolation",
    "SimValidator",
    "ValidationReport",
    "StagedRollout",
    "RolloutLog",
]
