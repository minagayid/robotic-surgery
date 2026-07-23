"""RobotX OS deterministic host-runtime reference implementation.

This package is intentionally dependency-free and offline-capable. It is not a
replacement for an independent hardware safety controller.
"""

from .contracts import (
    BodyState,
    ContractHeader,
    HealthSnapshot,
    MotionProposal,
    SafetyAction,
    SafetyDecision,
    SafetyLimits,
)
from .runtime import RobotRuntime
from .safety import SafetySupervisor

__all__ = [
    "BodyState",
    "ContractHeader",
    "HealthSnapshot",
    "MotionProposal",
    "RobotRuntime",
    "SafetyAction",
    "SafetyDecision",
    "SafetyLimits",
    "SafetySupervisor",
]
