"""Deterministic non-clinical scenarios for the reference runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .clock import DeterministicClock
from .contracts import MotionProposal, RobotState, SafetyLimits, SpatialObservation
from .events import EventJournal
from .movement import EXTREMITY_PROCESSORS, ExtremityProcessor, FiveHeartOrchestrator
from .runtime import OfflineRuntime
from .spatial import SpatialFusionEngine
from .workcell import DEFAULT_WORKCELL_PROFILE


def _runtime(journal_path: Path | str) -> tuple[OfflineRuntime, DeterministicClock]:
    clock = DeterministicClock(1_000_000_000)
    runtime = OfflineRuntime(
        clock=clock,
        limits=SafetyLimits(
            position_limits=((-1.0, 1.0), (-1.0, 1.0)),
            max_velocity=(0.5, 0.5),
            max_force_n=(5.0, 5.0),
            min_proximity_m=0.2,
            max_command_duration_ms=1_000,
        ),
        allowed_sources={"offline-planner"},
        journal=EventJournal(journal_path),
    )
    runtime.update_state(
        RobotState(
            timestamp_ns=clock.now_ns(),
            calibration_id="tabletop-calibration-v1",
            joint_positions=(0.0, 0.0),
            heartbeat_seq=1,
            proximity_m=1.0,
            sensor_health=(True, True),
        )
    )
    return runtime, clock


def _proposal(*, sequence: int, now_ns: int, target: tuple[float, float], velocities: tuple[float, float], expires_at_ns: int) -> MotionProposal:
    return MotionProposal(
        source_id="offline-planner",
        sequence=sequence,
        calibration_id="tabletop-calibration-v1",
        created_at_ns=now_ns - 10_000,
        expires_at_ns=expires_at_ns,
        duration_ms=500,
        target_positions=target,
        velocities=velocities,
        force_limits_n=(2.0, 2.0),
    )


def run_demo(journal_path: Path | str) -> dict[str, Any]:
    """Run approved, clamped, and rejected motion proposals offline."""
    runtime, clock = _runtime(journal_path)
    steps = []
    steps.append(runtime.submit(_proposal(sequence=1, now_ns=clock.now_ns(), target=(0.1, -0.1), velocities=(0.25, 0.25), expires_at_ns=clock.now_ns() + 1_000_000_000)))
    steps.append(runtime.submit(_proposal(sequence=2, now_ns=clock.now_ns(), target=(0.2, -0.2), velocities=(2.0, -2.0), expires_at_ns=clock.now_ns() + 1_000_000_000)))

    clock.advance_ns(50_000_000)
    if runtime.state is None:
        raise RuntimeError("demo runtime lost its simulated state")
    runtime.update_state(
        RobotState(
            timestamp_ns=clock.now_ns(),
            calibration_id=runtime.state.calibration_id,
            joint_positions=runtime.state.joint_positions,
            heartbeat_seq=2,
            proximity_m=runtime.state.proximity_m,
            sensor_health=runtime.state.sensor_health,
        )
    )
    steps.append(runtime.submit(_proposal(sequence=3, now_ns=clock.now_ns(), target=(0.25, -0.25), velocities=(0.25, 0.25), expires_at_ns=clock.now_ns())))

    return {
        "mode": "simulation_only",
        "steps": [decision.to_dict() for decision in steps],
        "final_joint_positions": list(runtime.state.joint_positions),
        "journal_verified": runtime.journal.verify(),
        "external_actions": [],
    }


def run_five_heart_demo(journal_path: Path | str) -> dict[str, Any]:
    """Exercise the four extremity, two regional, and main gates offline."""
    clock = DeterministicClock(1_000_000_000)
    limits = SafetyLimits(
        position_limits=((-1.0, 1.0), (-1.0, 1.0)),
        max_velocity=(0.5, 0.5),
        max_force_n=(5.0, 5.0),
        min_proximity_m=0.2,
        max_command_duration_ms=1_000,
    )
    runtime = OfflineRuntime(
        clock=clock,
        limits=SafetyLimits(
            position_limits=((-1.0, 1.0),) * 8,
            max_velocity=(0.5,) * 8,
            max_force_n=(5.0,) * 8,
            min_proximity_m=0.2,
            max_command_duration_ms=1_000,
        ),
        allowed_sources={f"offline-planner.{name}" for name in EXTREMITY_PROCESSORS},
        journal=EventJournal(journal_path),
    )
    runtime.update_state(
        RobotState(
            timestamp_ns=clock.now_ns(),
            calibration_id="tabletop-calibration-v1",
            joint_positions=(0.0,) * 8,
            heartbeat_seq=1,
            proximity_m=1.0,
            sensor_health=(True,) * 8,
        )
    )
    processors = {
        name: ExtremityProcessor(
            processor_id=name,
            joint_indices=(offset * 2, offset * 2 + 1),
            limits=limits,
            source_id=f"offline-planner.{name}",
        )
        for offset, name in enumerate(EXTREMITY_PROCESSORS)
    }
    orchestrator = FiveHeartOrchestrator(processors)
    spatial_snapshot = SpatialFusionEngine().fuse(
        [
            SpatialObservation(
                source_id="ultrasonic-front",
                modality="ultrasonic",
                region_id="workcell",
                timestamp_ns=clock.now_ns(),
                calibration_id="tabletop-calibration-v1",
                occupied=False,
                confidence=0.92,
            ),
            SpatialObservation(
                source_id="mmwave-front",
                modality="mmwave_radar",
                region_id="workcell",
                timestamp_ns=clock.now_ns(),
                calibration_id="tabletop-calibration-v1",
                occupied=False,
                confidence=0.90,
            ),
        ],
        now_ns=clock.now_ns(),
        calibration_id="tabletop-calibration-v1",
        region_id="workcell",
    )
    proposals = {
        name: MotionProposal(
            source_id=f"offline-planner.{name}",
            sequence=1,
            calibration_id="tabletop-calibration-v1",
            created_at_ns=clock.now_ns() - 1_000,
            expires_at_ns=clock.now_ns() + 1_000_000_000,
            duration_ms=500,
            target_positions=(0.1, -0.1),
            velocities=(0.25, 0.25),
            force_limits_n=(2.0, 2.0),
            actuator_group=name,
            orchestration_id="demo-bundle-1",
        )
        for name in EXTREMITY_PROCESSORS
    }
    decision = runtime.submit_orchestrated(
        orchestrator,
        proposals,
        spatial_snapshot=spatial_snapshot,
    )
    return {
        "mode": "simulation_only",
        "workcell": DEFAULT_WORKCELL_PROFILE.to_dict(),
        "architecture": {
            "extremity_processors": list(EXTREMITY_PROCESSORS),
            "regional_coordinators": {
                "upper": ["left_arm", "right_arm"],
                "lower": ["left_leg", "right_leg"],
            },
            "final_processor": "motion_orchestrator",
        },
        "spatial_snapshot": spatial_snapshot.to_dict(),
        "orchestration": decision.to_dict(),
        "final_joint_positions": list(runtime.state.joint_positions) if runtime.state else [],
        "journal_verified": runtime.journal.verify(),
        "external_actions": [],
    }
