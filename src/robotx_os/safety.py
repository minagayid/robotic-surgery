"""Fail-closed deterministic host-side motion supervisor."""

from __future__ import annotations

from .contracts import (
    BodyState,
    HealthSnapshot,
    MotionProposal,
    SafetyAction,
    SafetyDecision,
    SafetyLimits,
)


class SafetySupervisor:
    """Evaluate motion without learned logic or mutable runtime limits.

    STOP decisions latch. Clearing the latch requires a separate deliberate
    reset call after all reset preconditions are satisfied.
    """

    def __init__(self, limits: SafetyLimits) -> None:
        self._limits = limits
        self._stop_latched = False
        self._last_sequences: dict[str, int] = {}

    @property
    def stop_latched(self) -> bool:
        return self._stop_latched

    def evaluate(
        self,
        proposal: MotionProposal,
        state: BodyState,
        health: HealthSnapshot,
        now_ns: int,
    ) -> SafetyDecision:
        proposal_id = proposal.proposal_id

        if self._stop_latched:
            return self._decision(SafetyAction.STOP, "stop_latched", proposal_id, now_ns)
        if health.physical_estop_engaged:
            return self._stop("physical_estop", proposal_id, now_ns)
        if not health.hardware_safety_ready:
            return self._stop("hardware_safety_not_ready", proposal_id, now_ns)
        if not health.configuration_verified:
            return self._stop("configuration_unverified", proposal_id, now_ns)
        if now_ns < health.heartbeat_ns:
            return self._stop("heartbeat_from_future", proposal_id, now_ns)
        if now_ns - health.heartbeat_ns > self._limits.heartbeat_timeout_ns:
            return self._stop("heartbeat_stale", proposal_id, now_ns)

        header_errors = (*proposal.header.validation_errors(), *state.header.validation_errors())
        if header_errors:
            return self._stop(header_errors[0], proposal_id, now_ns)
        if not proposal_id:
            return self._decision(SafetyAction.REJECT, "missing_proposal_id", proposal_id, now_ns)
        if proposal.header.source_id not in self._limits.authorized_motion_sources:
            return self._decision(SafetyAction.REJECT, "unauthorized_motion_source", proposal_id, now_ns)
        if state.header.source_id not in self._limits.authorized_state_sources:
            return self._stop("unauthorized_state_source", proposal_id, now_ns)
        if proposal.header.confidence < self._limits.minimum_confidence:
            return self._decision(SafetyAction.REJECT, "proposal_low_confidence", proposal_id, now_ns)
        if state.header.confidence < self._limits.minimum_confidence:
            return self._stop("state_low_confidence", proposal_id, now_ns)
        if proposal.header.calibration_id != self._limits.calibration_id:
            return self._stop("proposal_calibration_mismatch", proposal_id, now_ns)
        if state.header.calibration_id != self._limits.calibration_id:
            return self._stop("state_calibration_mismatch", proposal_id, now_ns)

        state_age = now_ns - state.header.monotonic_ns
        if state_age < -self._limits.future_tolerance_ns:
            return self._stop("state_from_future", proposal_id, now_ns)
        if state_age > self._limits.state_timeout_ns:
            return self._stop("state_stale", proposal_id, now_ns)
        if proposal.header.monotonic_ns > now_ns + self._limits.future_tolerance_ns:
            return self._decision(SafetyAction.REJECT, "proposal_from_future", proposal_id, now_ns)
        if proposal.valid_until_ns < proposal.header.monotonic_ns:
            return self._decision(SafetyAction.REJECT, "invalid_validity_window", proposal_id, now_ns)
        if now_ns > proposal.valid_until_ns:
            return self._decision(SafetyAction.REJECT, "proposal_expired", proposal_id, now_ns)
        if not 0 < proposal.execution_duration_ns <= self._limits.max_command_duration_ns:
            return self._decision(SafetyAction.REJECT, "invalid_execution_duration", proposal_id, now_ns)
        if now_ns + proposal.execution_duration_ns > proposal.valid_until_ns:
            return self._decision(SafetyAction.REJECT, "execution_exceeds_expiry", proposal_id, now_ns)

        prior_sequence = self._last_sequences.get(proposal.header.source_id)
        if prior_sequence is not None and proposal.header.sequence <= prior_sequence:
            return self._decision(SafetyAction.REJECT, "replayed_or_out_of_order", proposal_id, now_ns)
        # Consume a well-formed sequence even when a later physical check rejects it.
        self._last_sequences[proposal.header.source_id] = proposal.header.sequence

        joint_count = self._limits.joint_count
        dimensions = (
            len(state.joint_positions),
            len(state.joint_velocities),
            len(state.joint_efforts),
            len(proposal.target_joint_velocities),
        )
        if any(size != joint_count for size in dimensions):
            return self._stop("joint_dimension_mismatch", proposal_id, now_ns)
        if not state.is_finite() or not proposal.is_finite():
            return self._stop("non_finite_numeric_input", proposal_id, now_ns)
        if state.nearest_obstacle_m < self._limits.minimum_obstacle_distance_m:
            return self._stop("obstacle_too_close", proposal_id, now_ns)

        for position, low, high in zip(
            state.joint_positions,
            self._limits.joint_position_min,
            self._limits.joint_position_max,
        ):
            if not low <= position <= high:
                return self._stop("joint_position_limit", proposal_id, now_ns)
        for effort, limit in zip(state.joint_efforts, self._limits.max_joint_effort):
            if abs(effort) > limit:
                return self._stop("joint_effort_limit", proposal_id, now_ns)

        bounded = tuple(
            max(-limit, min(requested, limit))
            for requested, limit in zip(
                proposal.target_joint_velocities,
                self._limits.max_joint_velocity,
            )
        )
        action = SafetyAction.CLAMP if bounded != proposal.target_joint_velocities else SafetyAction.APPROVE
        seconds = proposal.execution_duration_ns / 1_000_000_000
        predicted_positions = tuple(
            position + velocity * seconds
            for position, velocity in zip(state.joint_positions, bounded)
        )
        for predicted, low, high in zip(
            predicted_positions,
            self._limits.joint_position_min,
            self._limits.joint_position_max,
        ):
            if not low <= predicted <= high:
                return self._decision(
                    SafetyAction.REJECT,
                    "predicted_joint_position_limit",
                    proposal_id,
                    now_ns,
                )
        reason = "velocity_clamped" if action is SafetyAction.CLAMP else "all_checks_passed"
        return self._decision(
            action,
            reason,
            proposal_id,
            now_ns,
            bounded,
            proposal.execution_duration_ns,
        )

    def reset_stop(
        self,
        state: BodyState,
        health: HealthSnapshot,
        now_ns: int,
        *,
        operator_acknowledged: bool,
    ) -> bool:
        if not self._stop_latched:
            return True
        state_current = 0 <= now_ns - state.header.monotonic_ns <= self._limits.state_timeout_ns
        heartbeat_current = 0 <= now_ns - health.heartbeat_ns <= self._limits.heartbeat_timeout_ns
        nearly_still = all(
            abs(velocity) <= self._limits.reset_velocity_tolerance
            for velocity in state.joint_velocities
        )
        safe = (
            operator_acknowledged
            and not health.physical_estop_engaged
            and health.hardware_safety_ready
            and health.configuration_verified
            and state_current
            and heartbeat_current
            and nearly_still
            and state.nearest_obstacle_m >= self._limits.minimum_obstacle_distance_m
            and state.header.calibration_id == self._limits.calibration_id
        )
        if safe:
            self._stop_latched = False
        return safe

    def _stop(self, reason: str, proposal_id: str, now_ns: int) -> SafetyDecision:
        self._stop_latched = True
        return self._decision(SafetyAction.STOP, reason, proposal_id, now_ns)

    def _decision(
        self,
        action: SafetyAction,
        reason: str,
        proposal_id: str,
        now_ns: int,
        velocities: tuple[float, ...] = (),
        duration_ns: int = 0,
    ) -> SafetyDecision:
        return SafetyDecision(
            action=action,
            reason=reason,
            proposal_id=proposal_id,
            decided_at_ns=now_ns,
            approved_joint_velocities=velocities,
            approved_duration_ns=duration_ns,
            stop_latched=self._stop_latched,
        )
