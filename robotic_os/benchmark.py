"""Small local benchmark for the deterministic safety decision path."""

from __future__ import annotations

import time
from typing import Any

from .clock import DeterministicClock
from .contracts import MotionProposal, RobotState, SafetyLimits
from .safety import SafetySupervisor


def run_benchmark(iterations: int = 1_000) -> dict[str, Any]:
    if iterations < 1 or iterations > 100_000:
        raise ValueError("iterations must be between 1 and 100000")
    clock = DeterministicClock(1_000_000_000)
    supervisor = SafetySupervisor(
        limits=SafetyLimits(
            position_limits=((-1.0, 1.0), (-1.0, 1.0)),
            max_velocity=(1.0, 1.0),
            max_force_n=(5.0, 5.0),
            min_proximity_m=0.2,
            max_command_duration_ms=500,
        ),
        allowed_sources={"benchmark"},
        heartbeat_timeout_ns=100_000_000,
    )
    state = RobotState(
        timestamp_ns=clock.now_ns(),
        calibration_id="benchmark-calibration",
        joint_positions=(0.0, 0.0),
        heartbeat_seq=1,
        proximity_m=1.0,
        sensor_health=(True, True),
    )
    timings_ns: list[int] = []
    approved = 0
    for sequence in range(1, iterations + 1):
        proposal = MotionProposal(
            source_id="benchmark",
            sequence=sequence,
            calibration_id="benchmark-calibration",
            created_at_ns=clock.now_ns() - 1,
            expires_at_ns=clock.now_ns() + 200_000_000,
            duration_ms=100,
            target_positions=(0.0, 0.0),
            velocities=(0.1, 0.1),
            force_limits_n=(1.0, 1.0),
        )
        start = time.perf_counter_ns()
        decision = supervisor.authorize(proposal, state, now_ns=clock.now_ns())
        timings_ns.append(time.perf_counter_ns() - start)
        approved += int(decision.status == "approved")
    ordered = sorted(timings_ns)
    p50 = ordered[(len(ordered) - 1) // 2]
    p99 = ordered[min(len(ordered) - 1, (len(ordered) * 99 + 99) // 100 - 1)]
    return {
        "mode": "simulation_only",
        "iterations": iterations,
        "approved": approved,
        "p50_us": round(p50 / 1_000, 3),
        "p99_us": round(p99 / 1_000, 3),
        "hardware_or_network_access": False,
    }
