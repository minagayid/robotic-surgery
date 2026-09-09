"""Offline, simulation-only RobotX reference runtime.

This package is a host-side research reference. It does not contain hardware
drivers, real-time guarantees, surgical workflows, or actuator access.
"""

from .clock import DeterministicClock, MonotonicClock
from .context import AdvisoryContext, CompactionDecision, ContextCompactionPolicy
from .contracts import (
    MotionProposal,
    RobotState,
    SafetyDecision,
    SafetyLimits,
    SpatialObservation,
    SpatialSnapshot,
)
from .data import DatasetAdmissionDecision, OfflineDatasetManifest, OfflineDatasetRegistry
from .events import EventJournal
from .movement import (
    EXTREMITY_PROCESSORS,
    ORCHESTRATOR_PROCESSOR,
    ExtremityProcessor,
    FiveHeartOrchestrator,
    OrchestrationDecision,
    ProcessorDecision,
)
from .runtime import OfflineRuntime
from .safety import SafetySupervisor
from .spatial import SpatialFusionEngine

__all__ = [
    "DeterministicClock",
    "EventJournal",
    "AdvisoryContext",
    "CompactionDecision",
    "ContextCompactionPolicy",
    "DatasetAdmissionDecision",
    "EXTREMITY_PROCESSORS",
    "ExtremityProcessor",
    "FiveHeartOrchestrator",
    "MotionProposal",
    "MonotonicClock",
    "OfflineDatasetManifest",
    "OfflineDatasetRegistry",
    "OfflineRuntime",
    "ORCHESTRATOR_PROCESSOR",
    "OrchestrationDecision",
    "ProcessorDecision",
    "RobotState",
    "SafetyDecision",
    "SafetyLimits",
    "SafetySupervisor",
    "SpatialFusionEngine",
    "SpatialObservation",
    "SpatialSnapshot",
]
