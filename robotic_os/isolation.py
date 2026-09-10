"""Process-isolated safety-worker reference boundary."""

from __future__ import annotations

import multiprocessing as mp
from queue import Empty

from .contracts import MotionProposal, RobotState, SafetyDecision, SafetyLimits
from .hardware_safety import IndependentSafetyController


def _safety_worker(
    output: "mp.Queue[dict[str, object]]",
    limits: SafetyLimits,
    heartbeat_timeout_ns: int,
    proposal_data: dict[str, object],
    state: RobotState,
    now_ns: int,
) -> None:
    try:
        proposal = MotionProposal.from_dict(proposal_data)
        decision = IndependentSafetyController(
            limits=limits,
            heartbeat_timeout_ns=heartbeat_timeout_ns,
        ).authorize(proposal, state, now_ns=now_ns)
        output.put({"decision": decision.to_dict()})
    except Exception as exc:  # pragma: no cover - defensive child-process boundary
        output.put({"error": type(exc).__name__})


class IsolatedSafetyBoundary:
    """Run the independent gate outside the host process and fail closed."""

    def __init__(self, *, limits: SafetyLimits, heartbeat_timeout_ns: int, timeout_ms: int = 250) -> None:
        if timeout_ms < 1:
            raise ValueError("timeout_ms must be positive")
        self.limits = limits
        self.heartbeat_timeout_ns = heartbeat_timeout_ns
        self.timeout_ms = timeout_ms
        self._context = mp.get_context("spawn")

    def authorize(self, proposal: MotionProposal, state: RobotState, *, now_ns: int) -> SafetyDecision:
        output = self._context.Queue(maxsize=1)
        process = self._context.Process(
            target=_safety_worker,
            args=(output, self.limits, self.heartbeat_timeout_ns, proposal.to_dict(), state, now_ns),
            daemon=True,
        )
        process.start()
        process.join(self.timeout_ms / 1000.0)
        if process.is_alive():
            process.terminate()
            process.join(0.2)
            return self._fail_closed(proposal, now_ns, "safety_worker_timeout")
        try:
            response = output.get_nowait()
        except Empty:
            return self._fail_closed(proposal, now_ns, "safety_worker_no_response")
        if "error" in response:
            return self._fail_closed(proposal, now_ns, "safety_worker_error")
        data = response.get("decision")
        if not isinstance(data, dict):
            return self._fail_closed(proposal, now_ns, "safety_worker_invalid_response")
        return SafetyDecision(
            status=str(data["status"]),
            reasons=tuple(str(reason) for reason in data["reasons"]),
            source_id=str(data["source_id"]),
            sequence=int(data["sequence"]),
            timestamp_ns=int(data["timestamp_ns"]),
            effective_velocities=tuple(float(value) for value in data["effective_velocities"]),
        )

    @staticmethod
    def _fail_closed(proposal: MotionProposal, now_ns: int, reason: str) -> SafetyDecision:
        return SafetyDecision(
            status="stopped",
            reasons=(reason,),
            source_id=proposal.source_id,
            sequence=proposal.sequence,
            timestamp_ns=now_ns,
            effective_velocities=tuple(0.0 for _ in proposal.velocities),
        )
