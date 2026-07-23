"""Composition root for the deterministic RobotX host runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actuator import ActuatorBoundary
from .clock import Clock
from .contracts import BodyState, HealthSnapshot, MotionProposal, SafetyDecision, contract_to_dict
from .events import EventJournal
from .safety import SafetySupervisor


@dataclass(slots=True)
class RobotRuntime:
    clock: Clock
    supervisor: SafetySupervisor
    actuator: ActuatorBoundary
    journal: EventJournal

    def execute(
        self,
        proposal: MotionProposal,
        state: BodyState,
        health: HealthSnapshot,
    ) -> tuple[SafetyDecision, BodyState]:
        now_ns = self.clock.now_ns()
        decision = self.supervisor.evaluate(proposal, state, health, now_ns)
        resulting_state = self.actuator.apply(decision, state)
        self._record(
            "motion_decision",
            now_ns,
            {
                "proposal": contract_to_dict(proposal),
                "decision": contract_to_dict(decision),
                "state_before": contract_to_dict(state),
                "state_after": contract_to_dict(resulting_state),
            },
        )
        return decision, resulting_state

    def _record(self, kind: str, now_ns: int, payload: dict[str, Any]) -> None:
        self.journal.append(kind, now_ns, payload)
