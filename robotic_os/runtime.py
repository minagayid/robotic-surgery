"""Offline simulation runtime and the simulated actuator boundary."""

from __future__ import annotations

from typing import Mapping

from .clock import DeterministicClock, MonotonicClock
from .contracts import MotionProposal, RobotState, SafetyDecision, SafetyLimits, SpatialSnapshot
from .events import EventJournal
from .movement import FiveHeartOrchestrator, OrchestrationDecision
from .safety import SafetySupervisor


class OfflineRuntime:
    """Reference runtime that never opens a hardware or network connection."""

    def __init__(
        self,
        *,
        clock: DeterministicClock | MonotonicClock,
        limits: SafetyLimits,
        allowed_sources: set[str],
        journal: EventJournal,
    ) -> None:
        self.clock = clock
        self.supervisor = SafetySupervisor(
            limits=limits,
            allowed_sources=allowed_sources,
            heartbeat_timeout_ns=100_000_000,
        )
        self.journal = journal
        self.state: RobotState | None = None
        self._fresh_state_required = False

    def update_state(self, state: RobotState) -> None:
        if self.state is not None and state.timestamp_ns < self.state.timestamp_ns:
            raise ValueError("robot state timestamp moved backwards")
        self.state = state
        self._fresh_state_required = False
        self.journal.append({"type": "state", "state": state.to_dict()})

    def submit(self, proposal: MotionProposal) -> SafetyDecision:
        if self.state is None:
            decision = SafetyDecision("stopped", ("no_robot_state",), proposal.source_id, proposal.sequence, self.clock.now_ns(), tuple(0.0 for _ in proposal.velocities))
            self.journal.append({"type": "decision", "proposal": proposal.to_dict(), "decision": decision.to_dict()})
            return decision
        now_ns = self.clock.now_ns()
        if self.supervisor.stop_latched:
            decision = self.supervisor.authorize(proposal, self.state, now_ns=now_ns)
            self.journal.append({"type": "decision", "proposal": proposal.to_dict(), "decision": decision.to_dict()})
            return decision
        if self._fresh_state_required:
            decision = SafetyDecision("rejected", ("fresh_state_required_after_reset",), proposal.source_id, proposal.sequence, now_ns, tuple(0.0 for _ in proposal.velocities))
            self.journal.append({"type": "decision", "proposal": proposal.to_dict(), "decision": decision.to_dict()})
            return decision
        decision = self.supervisor.authorize(proposal, self.state, now_ns=now_ns)
        self.journal.append({"type": "decision", "proposal": proposal.to_dict(), "decision": decision.to_dict()})
        if decision.status in {"approved", "clamped"}:
            self.state = RobotState(
                timestamp_ns=now_ns,
                calibration_id=self.state.calibration_id,
                joint_positions=proposal.target_positions,
                heartbeat_seq=self.state.heartbeat_seq,
                proximity_m=self.state.proximity_m,
                sensor_health=self.state.sensor_health,
                emergency_stop=False,
            )
            self.journal.append({"type": "simulated_execution", "target_positions": list(proposal.target_positions), "status": decision.status})
        return decision

    def submit_orchestrated(
        self,
        orchestrator: FiveHeartOrchestrator,
        proposals: Mapping[str, MotionProposal],
        *,
        spatial_snapshot: SpatialSnapshot | None,
    ) -> OrchestrationDecision:
        """Submit a bundle through regional coordinators and the main gate."""
        now_ns = self.clock.now_ns()
        if self.state is None:
            decision = OrchestrationDecision(
                "stopped",
                "",
                now_ns,
                ("no_robot_state",),
                (),
                (),
            )
        elif self.supervisor.stop_latched or self.state.emergency_stop:
            if self.state.emergency_stop:
                self.supervisor.trigger_emergency_stop()
            decision = OrchestrationDecision(
                "stopped",
                "",
                now_ns,
                ("emergency_stop_latched",),
                (),
                (),
            )
        elif self._fresh_state_required:
            decision = OrchestrationDecision(
                "rejected",
                "",
                now_ns,
                ("fresh_state_required_after_reset",),
                (),
                (),
            )
        else:
            decision = orchestrator.orchestrate(
                proposals,
                self.state,
                spatial_snapshot=spatial_snapshot,
                now_ns=now_ns,
            )
            if decision.status in {"approved", "clamped"}:
                global_reasons: list[str] = []
                if len(decision.effective_target_positions) != len(self.supervisor.limits.position_limits):
                    global_reasons.append("runtime_joint_dimension_mismatch")
                else:
                    for item in decision.processor_decisions:
                        proposal = proposals[item.processor_id]
                        processor = orchestrator.processors[item.processor_id]
                        for index, target, force, velocity in zip(
                            processor.joint_indices,
                            proposal.target_positions,
                            proposal.force_limits_n,
                            item.decision.effective_velocities,
                        ):
                            low, high = self.supervisor.limits.position_limits[index]
                            if not low <= target <= high:
                                global_reasons.append(f"runtime_joint_{index}_position_limit")
                            if force > self.supervisor.limits.max_force_n[index]:
                                global_reasons.append(f"runtime_joint_{index}_force_limit")
                            if abs(velocity) > self.supervisor.limits.max_velocity[index]:
                                global_reasons.append(f"runtime_joint_{index}_velocity_limit")
                if global_reasons:
                    decision = OrchestrationDecision(
                        "rejected",
                        decision.orchestration_id,
                        now_ns,
                        tuple(dict.fromkeys(global_reasons)),
                        decision.processor_decisions,
                        (),
                    )
        self.journal.append({
            "type": "orchestration_decision",
            "decision": decision.to_dict(),
            "spatial_snapshot": spatial_snapshot.to_dict() if spatial_snapshot else None,
        })
        if self.state is not None and decision.status in {"approved", "clamped"}:
            self.state = RobotState(
                timestamp_ns=now_ns,
                calibration_id=self.state.calibration_id,
                joint_positions=decision.effective_target_positions,
                heartbeat_seq=self.state.heartbeat_seq,
                proximity_m=self.state.proximity_m,
                sensor_health=self.state.sensor_health,
                emergency_stop=False,
            )
            self.journal.append({
                "type": "simulated_orchestrated_execution",
                "target_positions": list(decision.effective_target_positions),
                "status": decision.status,
                "orchestration_id": decision.orchestration_id,
            })
        return decision

    def trigger_emergency_stop(self) -> None:
        self.supervisor.trigger_emergency_stop()
        self._fresh_state_required = True
        self.journal.append({"type": "emergency_stop", "status": "latched"})

    def reset(self, operator_id: str) -> bool:
        accepted = self.supervisor.reset(operator_id)
        self.journal.append({"type": "operator_reset", "accepted": accepted})
        return accepted
