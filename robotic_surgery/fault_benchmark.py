"""Deterministic fault injection against the existing simulation supervisor."""
from __future__ import annotations

from dataclasses import replace
import json

from .contracts import MotionProposal, RobotState, SafetyLimits
from .safety import SafetySupervisor


def run_fault_benchmark() -> dict:
    now = 1_000_000_000
    limits = SafetyLimits(((-1., 1.),) * 2, (.5, .5), (5., 5.), .2, 1000)
    state = RobotState(now, "fixture-v1", (0., 0.), 1, 1., (True, True))
    proposal = MotionProposal("fixture-planner", 1, "fixture-v1", now - 1000,
                              now + 1_000_000_000, 500, (.1, -.1), (.2, -.2), (2., 2.))
    cases = [
        ("healthy_control", proposal, state, "approved", None),
        ("sensor_dropout", proposal, replace(state, sensor_health=(False, True)), "rejected", "sensor_unhealthy"),
        ("latency_spike", proposal, replace(state, timestamp_ns=now - 200_000_000), "rejected", "stale_heartbeat"),
        ("invalid_pose_dimensions", proposal, replace(state, joint_positions=(0.,), sensor_health=(True,)), "rejected", "joint_dimension_mismatch"),
        ("out_of_workspace", replace(proposal, target_positions=(2., 0.)), state, "rejected", "joint_0_position_limit"),
        ("controller_fault", replace(proposal, source_id="untrusted-controller"), state, "rejected", "source_not_allowed"),
        ("emergency_stop", proposal, replace(state, emergency_stop=True), "stopped", "emergency_stop_latched"),
    ]
    rows = []
    for name, p, s, expected, reason in cases:
        supervisor = SafetySupervisor(limits=limits, allowed_sources={"fixture-planner"}, heartbeat_timeout_ns=100_000_000)
        decision = supervisor.authorize(p, s, now_ns=now)
        rows.append({"case": name, "decision": decision.to_dict(),
                     "passed": decision.status == expected and (reason is None or reason in decision.reasons)})
    supervisor = SafetySupervisor(limits=limits, allowed_sources={"fixture-planner"}, heartbeat_timeout_ns=100_000_000)
    supervisor.authorize(proposal, state, now_ns=now)
    replay = supervisor.authorize(proposal, state, now_ns=now)
    rows.append({"case": "command_replay", "decision": replay.to_dict(),
                 "passed": replay.status == "rejected" and "replayed_sequence" in replay.reasons})
    return {"schema_version": 1, "mode": "simulation-only", "external_actions": [],
            "scope": "eight deterministic fixtures; no hardware, tissue, clinical or device validation",
            "case_count": len(rows), "passed": sum(r["passed"] for r in rows), "cases": rows}


if __name__ == "__main__":
    result = run_fault_benchmark()
    print(json.dumps(result, indent=2))
    if result["passed"] != result["case_count"]:
        raise SystemExit(1)
