"""Microbenchmark for the host-side safety decision path.

This reports observed Python reference-runtime latency only. It is not a
hard-real-time timing guarantee and must not be used as a hardware safety claim.
"""

from __future__ import annotations

from statistics import mean
from time import perf_counter_ns

from robotx_os.contracts import (
    BodyState,
    ContractHeader,
    HealthSnapshot,
    MotionProposal,
    SafetyLimits,
)
from robotx_os.safety import SafetySupervisor


def percentile(sorted_samples: list[int], fraction: float) -> int:
    index = min(len(sorted_samples) - 1, int(len(sorted_samples) * fraction))
    return sorted_samples[index]


def main(iterations: int = 20_000) -> None:
    now_ns = 1_000_000_000
    calibration = "benchmark-cal-v1"
    supervisor = SafetySupervisor(
        SafetyLimits(
            calibration_id=calibration,
            authorized_motion_sources=("benchmark-planner",),
            authorized_state_sources=("benchmark-state",),
            joint_position_min=(-3.14,) * 7,
            joint_position_max=(3.14,) * 7,
            max_joint_velocity=(1.0,) * 7,
            max_joint_effort=(50.0,) * 7,
        )
    )
    state_header = ContractHeader(now_ns, "benchmark-state", calibration, 1)
    state = BodyState(
        state_header,
        (0.0,) * 7,
        (0.0,) * 7,
        (0.0,) * 7,
        2.0,
        True,
    )
    health = HealthSnapshot(
        now_ns,
        hardware_safety_ready=True,
        configuration_verified=True,
    )
    samples: list[int] = []
    for sequence in range(iterations):
        proposal_header = ContractHeader(
            now_ns, "benchmark-planner", calibration, sequence
        )
        proposal = MotionProposal(
            proposal_header,
            f"benchmark-{sequence}",
            now_ns + 20_000_000,
            (0.1,) * 7,
            10_000_000,
        )
        started = perf_counter_ns()
        supervisor.evaluate(proposal, state, health, now_ns)
        samples.append(perf_counter_ns() - started)

    samples.sort()
    print(f"iterations={iterations}")
    print(f"mean_us={mean(samples) / 1_000:.3f}")
    print(f"p50_us={percentile(samples, 0.50) / 1_000:.3f}")
    print(f"p95_us={percentile(samples, 0.95) / 1_000:.3f}")
    print(f"p99_us={percentile(samples, 0.99) / 1_000:.3f}")
    print(f"max_us={samples[-1] / 1_000:.3f}")


if __name__ == "__main__":
    main()
