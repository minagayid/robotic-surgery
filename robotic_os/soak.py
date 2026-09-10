"""Deterministic long-duration safety and fault-injection harness."""

from __future__ import annotations

import time
import hashlib
import json
from dataclasses import replace
from typing import Any

from .contracts import MotionProposal, RobotState, SafetyLimits
from .faults import FaultInjector
from .hardware_safety import IndependentSafetyController
from .safety import SafetySupervisor


def run_soak(*, iterations: int = 10_000, fault_interval: int = 1_000) -> dict[str, Any]:
    """Exercise both host and independent gates without external actuation."""
    if iterations < 1 or fault_interval < 1:
        raise ValueError("iterations and fault_interval must be positive")
    joint_count = 8
    limits = SafetyLimits(
        position_limits=tuple((-1.0, 1.0) for _ in range(joint_count)),
        max_velocity=tuple(1.0 for _ in range(joint_count)),
        max_force_n=tuple(5.0 for _ in range(joint_count)),
        min_proximity_m=0.2,
        max_command_duration_ms=500,
    )
    base_ns = 1_000_000_000
    state = RobotState(
        timestamp_ns=base_ns,
        calibration_id="soak-calibration",
        joint_positions=tuple(0.0 for _ in range(joint_count)),
        heartbeat_seq=1,
        proximity_m=1.0,
        sensor_health=tuple(True for _ in range(joint_count)),
    )
    supervisor = SafetySupervisor(
        limits=limits,
        allowed_sources={"soak-planner"},
        heartbeat_timeout_ns=100_000_000,
    )
    independent = IndependentSafetyController(limits=limits, heartbeat_timeout_ns=100_000_000)
    latencies_us: list[float] = []
    approved = 0
    fault_rejected = 0
    unexpected = 0
    for sequence in range(1, iterations + 1):
        now_ns = base_ns + sequence * 1_000_000_000
        proposal = MotionProposal(
            source_id="soak-planner",
            sequence=sequence,
            calibration_id="soak-calibration",
            created_at_ns=now_ns - 1,
            expires_at_ns=now_ns + 1_000_000_000,
            duration_ms=100,
            target_positions=tuple(0.0 for _ in range(joint_count)),
            velocities=tuple(0.1 for _ in range(joint_count)),
            force_limits_n=tuple(1.0 for _ in range(joint_count)),
        )
        current_state = replace(state, timestamp_ns=now_ns, heartbeat_seq=sequence)
        test_state = FaultInjector.unhealthy_sensor(current_state) if sequence % fault_interval == 0 else current_state
        started = time.perf_counter_ns()
        host_decision = supervisor.authorize(proposal, test_state, now_ns=now_ns)
        final_decision = independent.authorize(proposal, test_state, now_ns=now_ns)
        latencies_us.append((time.perf_counter_ns() - started) / 1_000.0)
        expected_fault = sequence % fault_interval == 0
        if expected_fault:
            if host_decision.status == "rejected" and final_decision.status == "rejected":
                fault_rejected += 1
            else:
                unexpected += 1
        elif host_decision.status in {"approved", "clamped"} and final_decision.status == "approved":
            approved += 1
        else:
            unexpected += 1
    ordered = sorted(latencies_us)
    p50 = ordered[(len(ordered) - 1) // 2]
    p99 = ordered[min(len(ordered) - 1, (len(ordered) * 99 + 99) // 100 - 1)]
    report = {
        "status": "pass" if unexpected == 0 else "fail",
        "iterations": iterations,
        "fault_interval": fault_interval,
        "approved": approved,
        "fault_rejected": fault_rejected,
        "unexpected": unexpected,
        "latency_us": {"p50": round(p50, 3), "p99": round(p99, 3)},
        "external_actuation": False,
        "deterministic_inputs": True,
        "simulated_duration_hours": round(iterations / 3_600.0, 6),
    }
    report["evidence_digest"] = soak_report_digest(report)
    return report


def soak_report_digest(report: dict[str, Any]) -> str:
    """Hash the report fields so a gate can detect edited evidence."""
    payload = {key: value for key, value in report.items() if key != "evidence_digest"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
