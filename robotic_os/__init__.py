"""Offline, simulation-only RobotX reference runtime.

This package is a host-side research reference. It does not contain hardware
drivers, real-time guarantees, surgical workflows, or actuator access.
"""

from .clock import DeterministicClock, MonotonicClock
from .adapters import ActuationReceipt, AdapterUnavailable, HardwareAbstractionLayer, ROS2AdapterContract, SimulationActuatorAdapter
from .calibration import CalibrationManifest, CalibrationRegistry
from .context import AdvisoryContext, CompactionDecision, ContextCompactionPolicy
from .contracts import (
    MotionProposal,
    RobotState,
    SafetyDecision,
    SafetyLimits,
    SpatialObservation,
    SpatialSnapshot,
)
from .spatial_4d import SpatialEntity, SpatialMeasurement, SpatialRecognitionSystem, SpatialWorldSnapshot
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
from .isolation import IsolatedSafetyBoundary
from .release_gate import GateCheck, ReleaseGateReport, evaluate_release, load_manifest
from .safety import SafetySupervisor
from .hardware_safety import IndependentSafetyController
from .spatial import SpatialFusionEngine
from .faults import FaultInjector
from .telemetry import TelemetryRecord, append_jsonl, read_jsonl
from .workcell import DEFAULT_WORKCELL_PROFILE, WorkcellProfile
from .soak import run_soak

__all__ = [
    "DeterministicClock",
    "ActuationReceipt",
    "AdapterUnavailable",
    "HardwareAbstractionLayer",
    "ROS2AdapterContract",
    "SimulationActuatorAdapter",
    "CalibrationManifest",
    "CalibrationRegistry",
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
    "IsolatedSafetyBoundary",
    "GateCheck",
    "ReleaseGateReport",
    "evaluate_release",
    "load_manifest",
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
    "SpatialEntity",
    "SpatialMeasurement",
    "SpatialRecognitionSystem",
    "SpatialWorldSnapshot",
    "TelemetryRecord",
    "append_jsonl",
    "read_jsonl",
    "WorkcellProfile",
    "DEFAULT_WORKCELL_PROFILE",
    "run_soak",
]
