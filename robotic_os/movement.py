"""Hierarchical movement path for the offline reference runtime.

The four extremity processors are independent deterministic validation gates.
Upper and lower coordinators aggregate their disjoint pairs without committing,
and the fifth logical processor is an atomic main orchestrator: it admits a
bundle only when all local, regional, and spatial gates agree. Nothing in this
module is a hardware driver or a clinical controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .contracts import (
    MotionProposal,
    RobotState,
    SafetyDecision,
    SafetyLimits,
    SpatialSnapshot,
    WAVE_SPATIAL_MODALITIES,
)
from .safety import SafetySupervisor


EXTREMITY_PROCESSORS = ("left_arm", "right_arm", "left_leg", "right_leg")
ORCHESTRATOR_PROCESSOR = "motion_orchestrator"
UPPER_COORDINATOR_PROCESSOR = "upper_coordinating_processor"
LOWER_COORDINATOR_PROCESSOR = "lower_coordinating_processor"
MAIN_COORDINATOR_PROCESSOR = ORCHESTRATOR_PROCESSOR
COORDINATION_GROUPS = {
    UPPER_COORDINATOR_PROCESSOR: ("left_arm", "right_arm"),
    LOWER_COORDINATOR_PROCESSOR: ("left_leg", "right_leg"),
}


@dataclass(frozen=True)
class ProcessorDecision:
    processor_id: str
    decision: SafetyDecision

    def to_dict(self) -> dict[str, object]:
        return {"processor_id": self.processor_id, "decision": self.decision.to_dict()}


@dataclass(frozen=True)
class CoordinatorDecision:
    """Result from an upper/lower regional coordination gate."""

    coordinator_id: str
    status: str
    reasons: tuple[str, ...]
    processor_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"approved", "clamped", "rejected", "stopped"}:
            raise ValueError("invalid coordinator status")
        if not self.coordinator_id or not self.processor_ids:
            raise ValueError("coordinator identity and processor IDs are required")

    def to_dict(self) -> dict[str, object]:
        return {
            "coordinator_id": self.coordinator_id,
            "status": self.status,
            "reasons": list(self.reasons),
            "processor_ids": list(self.processor_ids),
        }


@dataclass(frozen=True)
class OrchestrationDecision:
    status: str
    orchestration_id: str
    timestamp_ns: int
    reasons: tuple[str, ...]
    processor_decisions: tuple[ProcessorDecision, ...]
    effective_target_positions: tuple[float, ...]
    coordinator_decisions: tuple[CoordinatorDecision, ...] = ()
    active_processor_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"approved", "clamped", "rejected", "stopped"}:
            raise ValueError("invalid orchestration status")
        if self.timestamp_ns < 0:
            raise ValueError("timestamp_ns must be non-negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "processor_id": ORCHESTRATOR_PROCESSOR,
            "status": self.status,
            "orchestration_id": self.orchestration_id,
            "timestamp_ns": self.timestamp_ns,
            "reasons": list(self.reasons),
            "processor_decisions": [item.to_dict() for item in self.processor_decisions],
            "effective_target_positions": list(self.effective_target_positions),
            "coordinator_decisions": [item.to_dict() for item in self.coordinator_decisions],
            "active_processor_ids": list(self.active_processor_ids),
        }


class ExtremityProcessor:
    """One isolated local safety processor for one extremity's joints."""

    def __init__(
        self,
        *,
        processor_id: str,
        joint_indices: tuple[int, ...],
        limits: SafetyLimits,
        source_id: str,
        heartbeat_timeout_ns: int = 100_000_000,
    ) -> None:
        if processor_id not in EXTREMITY_PROCESSORS:
            raise ValueError("processor_id must name a supported extremity")
        if not joint_indices or len(set(joint_indices)) != len(joint_indices):
            raise ValueError("joint_indices must be non-empty and unique")
        if any(index < 0 for index in joint_indices):
            raise ValueError("joint_indices must be non-negative")
        if len(limits.position_limits) != len(joint_indices):
            raise ValueError("processor limits must match joint_indices")
        if not source_id.strip():
            raise ValueError("source_id must not be empty")
        self.processor_id = processor_id
        self.joint_indices = tuple(joint_indices)
        self.source_id = source_id
        self.supervisor = SafetySupervisor(
            limits=limits,
            allowed_sources={source_id},
            heartbeat_timeout_ns=heartbeat_timeout_ns,
        )

    def _local_state(self, state: RobotState) -> RobotState:
        if any(index >= len(state.joint_positions) for index in self.joint_indices):
            raise ValueError("processor joint index is outside robot state")
        return RobotState(
            timestamp_ns=state.timestamp_ns,
            calibration_id=state.calibration_id,
            joint_positions=tuple(state.joint_positions[index] for index in self.joint_indices),
            heartbeat_seq=state.heartbeat_seq,
            proximity_m=state.proximity_m,
            sensor_health=tuple(state.sensor_health[index] for index in self.joint_indices),
            emergency_stop=state.emergency_stop,
        )

    def validate(self, proposal: MotionProposal, state: RobotState, *, now_ns: int) -> ProcessorDecision:
        if proposal.actuator_group != self.processor_id:
            decision = SafetyDecision(
                "rejected",
                ("processor_group_mismatch",),
                proposal.source_id,
                proposal.sequence,
                now_ns,
                tuple(0.0 for _ in proposal.velocities),
            )
            return ProcessorDecision(self.processor_id, decision)
        if proposal.source_id != self.source_id:
            decision = SafetyDecision(
                "rejected",
                ("processor_source_mismatch",),
                proposal.source_id,
                proposal.sequence,
                now_ns,
                tuple(0.0 for _ in proposal.velocities),
            )
            return ProcessorDecision(self.processor_id, decision)
        if len(proposal.target_positions) != len(self.joint_indices):
            decision = SafetyDecision(
                "rejected",
                ("processor_joint_dimension_mismatch",),
                proposal.source_id,
                proposal.sequence,
                now_ns,
                tuple(0.0 for _ in proposal.velocities),
            )
            return ProcessorDecision(self.processor_id, decision)
        decision = self.supervisor.authorize(
            proposal,
            self._local_state(state),
            now_ns=now_ns,
            commit_sequence=False,
        )
        return ProcessorDecision(self.processor_id, decision)

    def commit(self, decision: ProcessorDecision) -> bool:
        return self.supervisor.commit_sequence(decision.decision.source_id, decision.decision.sequence)


class RegionalCoordinator:
    """Coordinate a disjoint pair without committing any processor state."""

    def __init__(self, coordinator_id: str, processor_ids: tuple[str, ...]) -> None:
        if coordinator_id not in COORDINATION_GROUPS:
            raise ValueError("unsupported regional coordinator")
        expected = COORDINATION_GROUPS[coordinator_id]
        if tuple(processor_ids) != expected:
            raise ValueError("regional coordinator must own its configured processors")
        self.coordinator_id = coordinator_id
        self.processor_ids = expected

    def coordinate(
        self,
        decisions: Mapping[str, ProcessorDecision],
        required_processor_ids: tuple[str, ...] | None = None,
    ) -> CoordinatorDecision:
        required = self.processor_ids if required_processor_ids is None else tuple(required_processor_ids)
        if not required or any(processor_id not in self.processor_ids for processor_id in required):
            raise ValueError("regional coordinator received an unsupported processor subset")
        missing = [processor_id for processor_id in required if processor_id not in decisions]
        if missing:
            return CoordinatorDecision(
                self.coordinator_id,
                "rejected",
                tuple(f"missing_processor:{processor_id}" for processor_id in missing),
                required,
            )
        selected = [decisions[processor_id] for processor_id in required]
        failures = [
            f"{item.processor_id}:{reason}"
            for item in selected
            if item.decision.status not in {"approved", "clamped"}
            for reason in item.decision.reasons
        ]
        if failures:
            return CoordinatorDecision(self.coordinator_id, "rejected", tuple(failures), required)
        status = "clamped" if any(item.decision.status == "clamped" for item in selected) else "approved"
        return CoordinatorDecision(self.coordinator_id, status, (), required)


class FiveHeartOrchestrator:
    """Atomically coordinate four extremity decisions through regional gates."""

    def __init__(
        self,
        processors: Mapping[str, ExtremityProcessor],
        *,
        min_spatial_confidence: float = 0.75,
        max_spatial_age_ns: int = 100_000_000,
    ) -> None:
        if set(processors) != set(EXTREMITY_PROCESSORS):
            raise ValueError("exactly four extremity processors are required")
        if not 0.0 < min_spatial_confidence <= 1.0:
            raise ValueError("min_spatial_confidence must be between 0 and 1")
        if max_spatial_age_ns < 1:
            raise ValueError("max_spatial_age_ns must be positive")
        indices = [index for processor in processors.values() for index in processor.joint_indices]
        if len(indices) != len(set(indices)):
            raise ValueError("extremity processors must own disjoint joints")
        self.processors = dict(processors)
        self.min_spatial_confidence = min_spatial_confidence
        self.max_spatial_age_ns = max_spatial_age_ns
        self._seen_orchestration_ids: set[str] = set()
        self.regional_coordinators = tuple(
            RegionalCoordinator(coordinator_id, processor_ids)
            for coordinator_id, processor_ids in COORDINATION_GROUPS.items()
        )

    @staticmethod
    def _rejected(
        *,
        orchestration_id: str,
        now_ns: int,
        reasons: list[str],
        processor_decisions: tuple[ProcessorDecision, ...] = (),
        coordinator_decisions: tuple[CoordinatorDecision, ...] = (),
        active_processor_ids: tuple[str, ...] = (),
    ) -> OrchestrationDecision:
        return OrchestrationDecision(
            "rejected",
            orchestration_id,
            now_ns,
            tuple(dict.fromkeys(reasons)),
            processor_decisions,
            (),
            coordinator_decisions,
            tuple(active_processor_ids),
        )

    def _spatial_reasons(
        self,
        snapshot: SpatialSnapshot | None,
        state: RobotState,
    ) -> list[str]:
        if snapshot is None:
            return ["spatial_evidence_missing"]
        reasons: list[str] = []
        if snapshot.calibration_id != state.calibration_id:
            reasons.append("spatial_calibration_mismatch")
        if snapshot.status != "clear":
            reasons.append("spatial_not_clear")
        if snapshot.confidence < self.min_spatial_confidence:
            reasons.append("spatial_confidence_below_threshold")
        if snapshot.timestamp_ns > state.timestamp_ns + self.max_spatial_age_ns:
            reasons.append("spatial_timestamp_ahead_of_state")
        if snapshot.timestamp_ns < state.timestamp_ns - self.max_spatial_age_ns:
            reasons.append("stale_spatial_snapshot")
        if len(set(snapshot.modality_ids)) < 2:
            reasons.append("insufficient_independent_modalities")
        if not set(snapshot.modality_ids) & WAVE_SPATIAL_MODALITIES:
            reasons.append("wave_evidence_missing")
        if snapshot.conflict:
            reasons.append("spatial_evidence_conflict")
        if snapshot.stop_required:
            reasons.append("spatial_stop_required")
        return reasons

    def orchestrate(
        self,
        proposals: Mapping[str, MotionProposal],
        state: RobotState,
        *,
        spatial_snapshot: SpatialSnapshot | None,
        now_ns: int,
        active_processors: tuple[str, ...] | None = None,
    ) -> OrchestrationDecision:
        """Validate and atomically admit a selective five-processor bundle.

        ``active_processors`` models the octopus-like case: a task may wake only
        the extremity brains it needs. Omitted extremities are held at their
        current joint positions and never receive a proposal or sequence commit.
        """
        if now_ns < 0:
            raise ValueError("now_ns must be non-negative")
        if active_processors is None:
            active = EXTREMITY_PROCESSORS
        else:
            requested = tuple(active_processors)
            if not requested or len(set(requested)) != len(requested) or any(
                processor_id not in EXTREMITY_PROCESSORS for processor_id in requested
            ):
                return self._rejected(
                    orchestration_id="",
                    now_ns=now_ns,
                    reasons=["invalid_active_processor_subset"],
                )
            active = tuple(processor_id for processor_id in EXTREMITY_PROCESSORS if processor_id in requested)
        keys = set(proposals)
        missing = sorted(set(active) - keys)
        unexpected = sorted(keys - set(active))
        if missing or unexpected:
            reasons = [
                *(f"missing_processor:{name}" for name in missing),
                *(f"inactive_or_unexpected_processor:{name}" for name in unexpected),
            ]
            return self._rejected(
                orchestration_id="",
                now_ns=now_ns,
                reasons=reasons,
                active_processor_ids=active,
            )

        ordered_proposals = [proposals[name] for name in active]
        orchestration_ids = {proposal.orchestration_id for proposal in ordered_proposals}
        if len(orchestration_ids) != 1 or not next(iter(orchestration_ids)):
            return self._rejected(
                orchestration_id="",
                now_ns=now_ns,
                reasons=["orchestration_id_missing_or_mismatched"],
                active_processor_ids=active,
            )
        orchestration_id = next(iter(orchestration_ids))
        if orchestration_id in self._seen_orchestration_ids:
            return self._rejected(
                orchestration_id=orchestration_id,
                now_ns=now_ns,
                reasons=["replayed_orchestration"],
                active_processor_ids=active,
            )
        self._seen_orchestration_ids.add(orchestration_id)

        spatial_reasons = self._spatial_reasons(spatial_snapshot, state)
        if spatial_reasons:
            return self._rejected(
                orchestration_id=orchestration_id,
                now_ns=now_ns,
                reasons=spatial_reasons,
                active_processor_ids=active,
            )

        try:
            decisions = tuple(
                self.processors[name].validate(proposals[name], state, now_ns=now_ns)
                for name in active
            )
        except ValueError:
            return self._rejected(
                orchestration_id=orchestration_id,
                now_ns=now_ns,
                reasons=["processor_state_incompatible"],
                active_processor_ids=active,
            )
        decision_map = {item.processor_id: item for item in decisions}
        coordinator_decisions = tuple(
            coordinator.coordinate(
                decision_map,
                tuple(processor_id for processor_id in coordinator.processor_ids if processor_id in active),
            )
            for coordinator in self.regional_coordinators
            if any(processor_id in active for processor_id in coordinator.processor_ids)
        )
        failed = [
            f"{item.processor_id}:{reason}"
            for item in decisions
            if item.decision.status not in {"approved", "clamped"}
            for reason in item.decision.reasons
        ]
        coordinator_failures = [
            f"{item.coordinator_id}:{reason}"
            for item in coordinator_decisions
            if item.status not in {"approved", "clamped"}
            for reason in item.reasons
        ]
        if failed or coordinator_failures:
            return self._rejected(
                orchestration_id=orchestration_id,
                now_ns=now_ns,
                reasons=[*failed, *coordinator_failures],
                processor_decisions=decisions,
                coordinator_decisions=coordinator_decisions,
                active_processor_ids=active,
            )

        effective_positions = list(state.joint_positions)
        for processor_id, item in zip(active, decisions):
            processor = self.processors[processor_id]
            for index, position in zip(processor.joint_indices, proposals[processor_id].target_positions):
                effective_positions[index] = position

        for processor_id, item in zip(active, decisions):
            if not self.processors[processor_id].commit(item):
                return self._rejected(
                    orchestration_id=orchestration_id,
                    now_ns=now_ns,
                    reasons=[f"{processor_id}:sequence_commit_failed"],
                    processor_decisions=decisions,
                    coordinator_decisions=coordinator_decisions,
                    active_processor_ids=active,
                )

        status = "clamped" if any(item.decision.status == "clamped" for item in decisions) else "approved"
        return OrchestrationDecision(
            status,
            orchestration_id,
            now_ns,
            (),
            decisions,
            tuple(effective_positions),
            coordinator_decisions,
            active,
        )
