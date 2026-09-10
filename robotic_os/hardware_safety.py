"""Independent final safety-gate model for SIL/HIL-style fault testing."""

from __future__ import annotations

from .contracts import MotionProposal, RobotState, SafetyDecision, SafetyLimits


class IndependentSafetyController:
    """A conservative reference of the controller that must sit below host code.

    This class is deliberately a pure simulation model. It is not a certified
    MCU/PLC implementation and has no connection to drives, power, or an
    emergency-stop circuit. Runtime commands must pass this final gate using
    the effective host command before the simulated state is advanced.
    """

    def __init__(self, *, limits: SafetyLimits, heartbeat_timeout_ns: int) -> None:
        if heartbeat_timeout_ns < 1:
            raise ValueError("heartbeat_timeout_ns must be positive")
        self.limits = limits
        self.heartbeat_timeout_ns = heartbeat_timeout_ns
        self._stop_latched = False
        self._last_sequences: dict[str, int] = {}

    @property
    def stop_latched(self) -> bool:
        return self._stop_latched

    def trigger_emergency_stop(self) -> None:
        self._stop_latched = True

    def reset(self, operator_id: str) -> bool:
        if not operator_id or not operator_id.strip():
            return False
        self._stop_latched = False
        return True

    def authorize(
        self,
        proposal: MotionProposal,
        state: RobotState,
        *,
        now_ns: int,
        commit_sequence: bool = True,
        joint_indices: tuple[int, ...] | None = None,
    ) -> SafetyDecision:
        if self._stop_latched or state.emergency_stop:
            if state.emergency_stop:
                self._stop_latched = True
            return self._decision("stopped", proposal, now_ns, ["independent_emergency_stop_latched"])

        reasons: list[str] = []
        if proposal.calibration_id != state.calibration_id:
            reasons.append("independent_calibration_mismatch")
        if state.timestamp_ns > now_ns:
            reasons.append("independent_future_state_timestamp")
        if now_ns - state.timestamp_ns > self.heartbeat_timeout_ns:
            reasons.append("independent_stale_heartbeat")
        if not all(state.sensor_health):
            reasons.append("independent_sensor_unhealthy")
        if state.proximity_m < self.limits.min_proximity_m:
            reasons.append("independent_unsafe_proximity")
        if now_ns < proposal.created_at_ns:
            reasons.append("independent_future_proposal")
        if now_ns >= proposal.expires_at_ns:
            reasons.append("independent_expired")
        if proposal.duration_ms > self.limits.max_command_duration_ms:
            reasons.append("independent_duration_exceeds_limit")
        if proposal.expires_at_ns - now_ns < proposal.duration_ms * 1_000_000:
            reasons.append("independent_expiry_before_completion")
        if proposal.sequence <= self._last_sequences.get(proposal.source_id, 0):
            reasons.append("independent_replayed_sequence")
        indices = joint_indices or tuple(range(len(self.limits.position_limits)))
        if len(proposal.target_positions) != len(indices) or any(index < 0 or index >= len(self.limits.position_limits) for index in indices):
            reasons.append("independent_joint_dimension_mismatch")
        else:
            for local_index, (index, target) in enumerate(zip(indices, proposal.target_positions)):
                low, high = self.limits.position_limits[index]
                if not low <= target <= high:
                    reasons.append(f"independent_joint_{index}_position_limit")
                predicted_velocity = abs(target - state.joint_positions[index]) / (proposal.duration_ms / 1000.0)
                if predicted_velocity > self.limits.max_velocity[index]:
                    reasons.append(f"independent_joint_{index}_predicted_velocity_limit")
            for index, velocity in zip(indices, proposal.velocities):
                if abs(velocity) > self.limits.max_velocity[index]:
                    reasons.append(f"independent_joint_{index}_velocity_limit")
            for index, force in zip(indices, proposal.force_limits_n):
                if force > self.limits.max_force_n[index]:
                    reasons.append(f"independent_joint_{index}_force_limit")
        if reasons:
            return self._decision("rejected", proposal, now_ns, reasons)
        if commit_sequence:
            self._last_sequences[proposal.source_id] = proposal.sequence
        return self._decision("approved", proposal, now_ns, [], proposal.velocities)

    def commit_sequence(self, source_id: str, sequence: int) -> bool:
        if sequence <= self._last_sequences.get(source_id, 0):
            return False
        self._last_sequences[source_id] = sequence
        return True

    @staticmethod
    def _decision(
        status: str,
        proposal: MotionProposal,
        now_ns: int,
        reasons: list[str],
        velocities: tuple[float, ...] | None = None,
    ) -> SafetyDecision:
        return SafetyDecision(
            status=status,
            reasons=tuple(dict.fromkeys(reasons)),
            source_id=proposal.source_id,
            sequence=proposal.sequence,
            timestamp_ns=now_ns,
            effective_velocities=velocities or tuple(0.0 for _ in proposal.velocities),
        )
