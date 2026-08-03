"""Fail-closed safety supervisor for the host-side simulator."""

from __future__ import annotations

from typing import Iterable

from .contracts import MotionProposal, RobotState, SafetyDecision, SafetyLimits


class SafetySupervisor:
    """Validate short-horizon motion proposals against deterministic limits.

    This is a reference implementation for simulation and testing. It is not a
    certified safety controller and cannot replace an independent MCU, PLC,
    drive safety function, or physical emergency stop.
    """

    def __init__(
        self,
        *,
        limits: SafetyLimits,
        allowed_sources: Iterable[str],
        heartbeat_timeout_ns: int,
    ) -> None:
        if heartbeat_timeout_ns < 1:
            raise ValueError("heartbeat_timeout_ns must be positive")
        self.limits = limits
        self.allowed_sources = frozenset(str(source) for source in allowed_sources if str(source))
        if not self.allowed_sources:
            raise ValueError("at least one allowed source is required")
        self.heartbeat_timeout_ns = int(heartbeat_timeout_ns)
        self._last_sequences: dict[str, int] = {}
        self._stop_latched = False

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

    def _decision(self, status: str, proposal: MotionProposal, now_ns: int, reasons: list[str], velocities: tuple[float, ...] | None = None) -> SafetyDecision:
        return SafetyDecision(
            status=status,
            reasons=tuple(dict.fromkeys(reasons)),
            source_id=proposal.source_id,
            sequence=proposal.sequence,
            timestamp_ns=now_ns,
            effective_velocities=velocities or tuple(0.0 for _ in proposal.velocities),
        )

    def authorize(self, proposal: MotionProposal, state: RobotState, *, now_ns: int) -> SafetyDecision:
        if self._stop_latched or state.emergency_stop:
            if state.emergency_stop:
                self._stop_latched = True
            return self._decision("stopped", proposal, now_ns, ["emergency_stop_latched"])

        reasons: list[str] = []
        if proposal.source_id not in self.allowed_sources:
            reasons.append("source_not_allowed")
        if proposal.calibration_id != state.calibration_id:
            reasons.append("calibration_mismatch")
        if state.timestamp_ns > now_ns:
            reasons.append("future_state_timestamp")
        if now_ns - state.timestamp_ns > self.heartbeat_timeout_ns:
            reasons.append("stale_heartbeat")
        if not all(state.sensor_health):
            reasons.append("sensor_unhealthy")
        if state.proximity_m < self.limits.min_proximity_m:
            reasons.append("unsafe_proximity")
        if now_ns < proposal.created_at_ns:
            reasons.append("future_timestamp")
        if now_ns >= proposal.expires_at_ns:
            reasons.append("expired")
        if proposal.duration_ms > self.limits.max_command_duration_ms:
            reasons.append("duration_exceeds_limit")
        if proposal.expires_at_ns - now_ns < proposal.duration_ms * 1_000_000:
            reasons.append("expiry_before_completion")
        if proposal.sequence <= self._last_sequences.get(proposal.source_id, 0):
            reasons.append("replayed_sequence")

        if len(proposal.target_positions) != len(state.joint_positions):
            reasons.append("joint_dimension_mismatch")

        if reasons:
            return self._decision("rejected", proposal, now_ns, reasons)

        for index, (position, bounds) in enumerate(zip(state.joint_positions, self.limits.position_limits)):
            target = proposal.target_positions[index]
            low, high = bounds
            if not low <= target <= high:
                reasons.append(f"joint_{index}_position_limit")
            predicted_velocity = abs(target - position) / (proposal.duration_ms / 1000.0)
            if predicted_velocity > self.limits.max_velocity[index]:
                reasons.append(f"joint_{index}_predicted_velocity_limit")
        for index, force in enumerate(proposal.force_limits_n):
            if force > self.limits.max_force_n[index]:
                reasons.append(f"joint_{index}_force_limit")

        clamped = tuple(
            max(-limit, min(limit, velocity))
            for velocity, limit in zip(proposal.velocities, self.limits.max_velocity)
        )
        reasons = [
            f"joint_{index}_velocity_clamped"
            for index, (requested, effective) in enumerate(zip(proposal.velocities, clamped))
            if requested != effective
        ]
        self._last_sequences[proposal.source_id] = proposal.sequence
        return self._decision("clamped" if reasons else "approved", proposal, now_ns, reasons, clamped)
