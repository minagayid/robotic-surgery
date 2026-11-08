"""Vendor-neutral tactile records and deterministic dexterity trial metrics.

This module is an early research reference for benchmark interoperability.
It does not acquire sensor data, control a robot, validate a sensor, or establish
clinical or physical safety.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import statistics
from collections.abc import Iterable, Mapping
from typing import Any


TACTILE_SCHEMA_VERSION = "0.1.0"
TACTILE_UNITS = {"force": "N", "torque": "N*m", "time": "ns"}


def _identifier(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _non_negative_integer(value: int, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _vector3(values: Iterable[float], field_name: str, *, non_negative: bool = False) -> tuple[float, float, float]:
    try:
        vector = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain three numeric values") from exc
    if len(vector) != 3:
        raise ValueError(f"{field_name} must contain exactly three values")
    normalized: list[float] = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} values must be numeric")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{field_name} values must be finite")
        if non_negative and number < 0:
            raise ValueError(f"{field_name} values must be non-negative")
        normalized.append(number)
    return (normalized[0], normalized[1], normalized[2])


@dataclass(frozen=True, slots=True)
class TactileFrame:
    """One calibrated tactile/force sample expressed in explicit SI units."""

    sensor_id: str
    sensor_model: str
    timestamp_ns: int
    sequence: int
    calibration_id: str
    coordinate_frame: str
    force_n: tuple[float, float, float]
    torque_nm: tuple[float, float, float]
    force_uncertainty_n: tuple[float, float, float]
    torque_uncertainty_nm: tuple[float, float, float]
    contact_probability: float

    def __post_init__(self) -> None:
        for field_name in ("sensor_id", "sensor_model", "calibration_id", "coordinate_frame"):
            object.__setattr__(self, field_name, _identifier(getattr(self, field_name), field_name))
        _non_negative_integer(self.timestamp_ns, "timestamp_ns")
        _non_negative_integer(self.sequence, "sequence")
        object.__setattr__(self, "force_n", _vector3(self.force_n, "force_n"))
        object.__setattr__(self, "torque_nm", _vector3(self.torque_nm, "torque_nm"))
        object.__setattr__(
            self,
            "force_uncertainty_n",
            _vector3(self.force_uncertainty_n, "force_uncertainty_n", non_negative=True),
        )
        object.__setattr__(
            self,
            "torque_uncertainty_nm",
            _vector3(self.torque_uncertainty_nm, "torque_uncertainty_nm", non_negative=True),
        )
        probability = self.contact_probability
        if isinstance(probability, bool) or not isinstance(probability, (int, float)):
            raise ValueError("contact_probability must be numeric")
        probability = float(probability)
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError("contact_probability must be finite and between 0 and 1")
        object.__setattr__(self, "contact_probability", probability)

    def to_record(self) -> dict[str, Any]:
        """Serialize a stable, versioned record with explicit units."""
        return {
            "schema_version": TACTILE_SCHEMA_VERSION,
            "sensor": {"id": self.sensor_id, "model": self.sensor_model},
            "time": {"timestamp_ns": self.timestamp_ns, "sequence": self.sequence},
            "calibration_id": self.calibration_id,
            "coordinate_frame": self.coordinate_frame,
            "units": dict(TACTILE_UNITS),
            "force_n": list(self.force_n),
            "torque_nm": list(self.torque_nm),
            "force_uncertainty_n": list(self.force_uncertainty_n),
            "torque_uncertainty_nm": list(self.torque_uncertainty_nm),
            "contact_probability": self.contact_probability,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> TactileFrame:
        """Parse the published v0.1 record shape, failing closed on schema drift."""
        if not isinstance(record, Mapping):
            raise ValueError("tactile record must be a mapping")
        if record.get("schema_version") != TACTILE_SCHEMA_VERSION:
            raise ValueError("unsupported tactile schema_version")
        if record.get("units") != TACTILE_UNITS:
            raise ValueError("tactile record must use the declared SI units")
        sensor = record.get("sensor")
        timing = record.get("time")
        if not isinstance(sensor, Mapping) or not isinstance(timing, Mapping):
            raise ValueError("tactile record requires sensor and time objects")
        try:
            return cls(
                sensor_id=sensor["id"],
                sensor_model=sensor["model"],
                timestamp_ns=timing["timestamp_ns"],
                sequence=timing["sequence"],
                calibration_id=record["calibration_id"],
                coordinate_frame=record["coordinate_frame"],
                force_n=tuple(record["force_n"]),
                torque_nm=tuple(record["torque_nm"]),
                force_uncertainty_n=tuple(record["force_uncertainty_n"]),
                torque_uncertainty_nm=tuple(record["torque_uncertainty_nm"]),
                contact_probability=record["contact_probability"],
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"malformed tactile record: {exc}") from exc


@dataclass(frozen=True, slots=True)
class DexterityTrial:
    """A single benchmark trial with provenance-linked tactile frames."""

    trial_id: str
    task_id: str
    platform_id: str
    started_at_ns: int
    finished_at_ns: int
    success: bool
    operator_interventions: int
    dropped_objects: int
    tactile_frames: tuple[TactileFrame, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("trial_id", "task_id", "platform_id"):
            object.__setattr__(self, field_name, _identifier(getattr(self, field_name), field_name))
        _non_negative_integer(self.started_at_ns, "started_at_ns")
        _non_negative_integer(self.finished_at_ns, "finished_at_ns")
        if self.finished_at_ns <= self.started_at_ns:
            raise ValueError("finished_at_ns must be later than started_at_ns")
        if type(self.success) is not bool:
            raise ValueError("success must be a boolean")
        _non_negative_integer(self.operator_interventions, "operator_interventions")
        _non_negative_integer(self.dropped_objects, "dropped_objects")
        frames = tuple(self.tactile_frames)
        if any(not isinstance(frame, TactileFrame) for frame in frames):
            raise ValueError("tactile_frames must contain TactileFrame values")
        last_by_sensor: dict[str, tuple[int, int]] = {}
        for frame in frames:
            if not self.started_at_ns <= frame.timestamp_ns <= self.finished_at_ns:
                raise ValueError("tactile frame timestamp is outside the trial window")
            previous = last_by_sensor.get(frame.sensor_id)
            if previous and (frame.timestamp_ns <= previous[0] or frame.sequence <= previous[1]):
                raise ValueError("tactile timestamps and sequences must increase per sensor")
            last_by_sensor[frame.sensor_id] = (frame.timestamp_ns, frame.sequence)
        object.__setattr__(self, "tactile_frames", frames)

    @property
    def duration_s(self) -> float:
        return (self.finished_at_ns - self.started_at_ns) / 1_000_000_000


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    """Deterministic summary metrics for repeated trials of one task protocol."""

    task_id: str
    trial_count: int
    success_count: int
    success_rate: float
    median_duration_s: float
    mean_operator_interventions: float
    drop_rate: float
    tactile_frame_count: int
    max_peak_force_n: float | None
    p95_peak_force_n: float | None
    force_limit_exceedance_count: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_trials(
    trials: Iterable[DexterityTrial],
    *,
    force_limit_n: float | None = None,
) -> BenchmarkSummary:
    """Summarize repeated trials; force limit is a benchmark parameter, not a safety limit."""
    items = tuple(trials)
    if not items:
        raise ValueError("at least one trial is required")
    if any(not isinstance(item, DexterityTrial) for item in items):
        raise ValueError("trials must contain DexterityTrial values")
    trial_ids = [item.trial_id for item in items]
    if len(set(trial_ids)) != len(trial_ids):
        raise ValueError("trial_id values must be unique")
    task_ids = {item.task_id for item in items}
    if len(task_ids) != 1:
        raise ValueError("all trials must use the same task_id")
    if force_limit_n is not None:
        if isinstance(force_limit_n, bool) or not isinstance(force_limit_n, (int, float)):
            raise ValueError("force_limit_n must be numeric")
        force_limit_n = float(force_limit_n)
        if not math.isfinite(force_limit_n) or force_limit_n <= 0:
            raise ValueError("force_limit_n must be finite and positive")

    force_magnitudes = [
        math.sqrt(sum(component * component for component in frame.force_n))
        for item in items
        for frame in item.tactile_frames
    ]
    frame_count = sum(len(item.tactile_frames) for item in items)
    success_count = sum(item.success for item in items)
    durations = [item.duration_s for item in items]
    total_interventions = sum(item.operator_interventions for item in items)
    trials_with_drop = sum(item.dropped_objects > 0 for item in items)
    exceedances = (
        sum(force > force_limit_n for force in force_magnitudes)
        if force_limit_n is not None
        else None
    )
    sorted_forces = sorted(force_magnitudes)
    p95 = sorted_forces[math.ceil(0.95 * len(sorted_forces)) - 1] if sorted_forces else None

    return BenchmarkSummary(
        task_id=next(iter(task_ids)),
        trial_count=len(items),
        success_count=success_count,
        success_rate=success_count / len(items),
        median_duration_s=float(statistics.median(durations)),
        mean_operator_interventions=total_interventions / len(items),
        drop_rate=trials_with_drop / len(items),
        tactile_frame_count=frame_count,
        max_peak_force_n=max(force_magnitudes) if force_magnitudes else None,
        p95_peak_force_n=p95,
        force_limit_exceedance_count=exceedances,
    )
