"""Five-processor movement path for the offline reference runtime.

The four extremity processors are independent deterministic validation gates.
The fifth processor is an atomic orchestrator: it admits a bundle only when
all four local decisions and the spatial evidence gate agree. Nothing in this
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


@dataclass(frozen=True)
class ProcessorDecision:
    processor_id: str
    decision: SafetyDecision

    def to_dict(self) -> dict[str, object]:
        return {"processor_id": self.processor_id, "decision": self.decision.to_dict()}


@dataclass(frozen=True)
class OrchestrationDecision:
    status: str
    orchestration_id: str
    timestamp_ns: int
    reasons: tuple[str, ...]
    processor_decisions: tuple[ProcessorDecision, ...]
    effective_target_positions: tuple[float, ...]

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


class FiveHeartOrchestrator:
    """Atomically coordinate four extremity decisions through a fifth gate."""

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

    @staticmethod
    def _rejected(
        *,
        orchestration_id: str,
        now_ns: int,
        reasons: list[str],
        processor_decisions: tuple[ProcessorDecision, ...] = (),
    ) -> OrchestrationDecision:
        return OrchestrationDecision(
            "rejected",
            orchestration_id,
            now_ns,
            tuple(dict.fromkeys(reasons)),
            processor_decisions,
            (),
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
    ) -> OrchestrationDecision:
        """Validate and atomically admit a complete five-processor bundle."""
        if now_ns < 0:
            raise ValueError("now_ns must be non-negative")
        keys = set(proposals)
        missing = sorted(set(EXTREMITY_PROCESSORS) - keys)
        unexpected = sorted(keys - set(EXTREMITY_PROCESSORS))
        if missing or unexpected:
            reasons = [*(f"missing_processor:{name}" for name in missing), *(f"unexpected_processor:{name}" for name in unexpected)]
            return self._rejected(orchestration_id="", now_ns=now_ns, reasons=reasons)

        ordered_proposals = [proposals[name] for name in EXTREMITY_PROCESSORS]
        orchestration_ids = {proposal.orchestration_id for proposal in ordered_proposals}
        if len(orchestration_ids) != 1 or not next(iter(orchestration_ids)):
            return self._rejected(orchestration_id="", now_ns=now_ns, reasons=["orchestration_id_missing_or_mismatched"])
        orchestration_id = next(iter(orchestration_ids))
        if orchestration_id in self._seen_orchestration_ids:
            return self._rejected(orchestration_id=orchestration_id, now_ns=now_ns, reasons=["replayed_orchestration"])
        self._seen_orchestration_ids.add(orchestration_id)

        spatial_reasons = self._spatial_reasons(spatial_snapshot, state)
        if spatial_reasons:
            return self._rejected(orchestration_id=orchestration_id, now_ns=now_ns, reasons=spatial_reasons)

        try:
            decisions = tuple(
                self.processors[name].validate(proposals[name], state, now_ns=now_ns)
                for name in EXTREMITY_PROCESSORS
            )
        except ValueError:
            return self._rejected(
                orchestration_id=orchestration_id,
                now_ns=now_ns,
                reasons=["processor_state_incompatible"],
            )
        failed = [
            f"{item.processor_id}:{reason}"
            for item in decisions
            if item.decision.status not in {"approved", "clamped"}
            for reason in item.decision.reasons
        ]
        if failed:
            return self._rejected(
                orchestration_id=orchestration_id,
                now_ns=now_ns,
                reasons=failed,
                processor_decisions=decisions,
            )

        effective_positions = list(state.joint_positions)
        for processor_id, item in zip(EXTREMITY_PROCESSORS, decisions):
            processor = self.processors[processor_id]
            for index, position in zip(processor.joint_indices, proposals[processor_id].target_positions):
                effective_positions[index] = position

        for processor_id, item in zip(EXTREMITY_PROCESSORS, decisions):
            if not self.processors[processor_id].commit(item):
                return self._rejected(
                    orchestration_id=orchestration_id,
                    now_ns=now_ns,
                    reasons=[f"{processor_id}:sequence_commit_failed"],
                    processor_decisions=decisions,
                )

        status = "clamped" if any(item.decision.status == "clamped" for item in decisions) else "approved"
        return OrchestrationDecision(
            status,
            orchestration_id,
            now_ns,
            (),
            decisions,
            tuple(effective_positions),
        )
