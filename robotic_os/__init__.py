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
    COORDINATION_GROUPS,
    EXTREMITY_PROCESSORS,
    LOWER_COORDINATOR_PROCESSOR,
    MAIN_COORDINATOR_PROCESSOR,
    ORCHESTRATOR_PROCESSOR,
    UPPER_COORDINATOR_PROCESSOR,
    CoordinatorDecision,
    ExtremityProcessor,
    FiveHeartOrchestrator,
    OrchestrationDecision,
    ProcessorDecision,
    RegionalCoordinator,
)
from .runtime import OfflineRuntime
from .safety import SafetySupervisor
from .hardware_safety import IndependentSafetyController
from .spatial import SpatialFusionEngine
from .faults import FaultInjector
from .telemetry import TelemetryRecord, append_jsonl, read_jsonl
from .workcell import DEFAULT_WORKCELL_PROFILE, WorkcellProfile

__all__ = [
    "DeterministicClock",
    "EventJournal",
    "AdvisoryContext",
    "CompactionDecision",
    "ContextCompactionPolicy",
    "COORDINATION_GROUPS",
    "DatasetAdmissionDecision",
    "EXTREMITY_PROCESSORS",
    "UPPER_COORDINATOR_PROCESSOR",
    "LOWER_COORDINATOR_PROCESSOR",
    "MAIN_COORDINATOR_PROCESSOR",
    "ExtremityProcessor",
    "FiveHeartOrchestrator",
    "MotionProposal",
    "MonotonicClock",
    "OfflineDatasetManifest",
    "OfflineDatasetRegistry",
    "OfflineRuntime",
    "IndependentSafetyController",
    "FaultInjector",
    "ORCHESTRATOR_PROCESSOR",
    "OrchestrationDecision",
    "ProcessorDecision",
    "CoordinatorDecision",
    "RegionalCoordinator",
    "RobotState",
    "SafetyDecision",
    "SafetyLimits",
    "SafetySupervisor",
    "SpatialFusionEngine",
    "SpatialObservation",
    "SpatialSnapshot",
    "TelemetryRecord",
    "append_jsonl",
    "read_jsonl",
    "WorkcellProfile",
    "DEFAULT_WORKCELL_PROFILE",
]
