"""Deterministic 360-degree, 4D spatial recognition reference slice.

This module is deliberately transport- and hardware-free. It turns timestamped
sensor evidence into an immutable world snapshot while keeping direct
observations, occluded inference, uncertainty, and emission policy explicit.
It is suitable for simulation and replay tests; it is not a sensor driver or a
clinical perception controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .contracts import SpatialSnapshot


SPATIAL_4D_MODALITIES = frozenset(
    {
        "rgb",
        "nir",
        "thermal",
        "lidar",
        "mmwave_radar",
        "ultrasonic",
        "microphone",
        "wifi_csi",
        "imu",
    }
)
PASSIVE_MODALITIES = frozenset({"rgb", "nir", "thermal", "microphone", "wifi_csi", "imu"})
ACTIVE_MODALITIES = frozenset({"lidar", "mmwave_radar", "ultrasonic"})
WAVE_MODALITIES = frozenset({"mmwave_radar", "ultrasonic", "wifi_csi"})
MODE_ACTIVE_MODALITIES = {
    "eco": frozenset({"lidar"}),
    "normal": ACTIVE_MODALITIES,
    "degraded": ACTIVE_MODALITIES,
}


def _vector(values: Iterable[float], name: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3:
        raise ValueError(f"{name} must contain exactly three values")
    if any(value != value or value in (float("inf"), float("-inf")) for value in result):
        raise ValueError(f"{name} must contain finite values")
    return result  # type: ignore[return-value]


@dataclass(frozen=True)
class SpatialMeasurement:
    """One sensor measurement in the common robot/world frame."""

    source_id: str
    modality: str
    region_id: str
    sector_index: int
    timestamp_ns: int
    calibration_id: str
    object_id: str
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    confidence: float
    occupied: bool
    observed: bool = True
    occluded: bool = False
    healthy: bool = True
    emits_energy: bool = False
    sequence: int = 1

    def __post_init__(self) -> None:
        if not self.source_id or not self.region_id or not self.calibration_id:
            raise ValueError("measurement identity fields must not be empty")
        if self.modality not in SPATIAL_4D_MODALITIES:
            raise ValueError("unsupported 4D spatial modality")
        if not self.object_id or len(self.object_id) > 120:
            raise ValueError("object_id must be a non-empty short identifier")
        if self.sector_index < 0 or self.timestamp_ns < 0 or self.sequence < 1:
            raise ValueError("sector, timestamp, and sequence are invalid")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not isinstance(self.occupied, bool) or not isinstance(self.observed, bool):
            raise ValueError("occupied and observed must be booleans")
        if not isinstance(self.occluded, bool) or not isinstance(self.healthy, bool):
            raise ValueError("occluded and healthy must be booleans")
        if not isinstance(self.emits_energy, bool):
            raise ValueError("emits_energy must be a boolean")
        object.__setattr__(self, "position", _vector(self.position, "position"))
        object.__setattr__(self, "velocity", _vector(self.velocity, "velocity"))
        object.__setattr__(self, "confidence", float(self.confidence))

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "modality": self.modality,
            "region_id": self.region_id,
            "sector_index": self.sector_index,
            "timestamp_ns": self.timestamp_ns,
            "calibration_id": self.calibration_id,
            "object_id": self.object_id,
            "position": list(self.position),
            "velocity": list(self.velocity),
            "confidence": self.confidence,
            "occupied": self.occupied,
            "observed": self.observed,
            "occluded": self.occluded,
            "healthy": self.healthy,
            "emits_energy": self.emits_energy,
            "sequence": self.sequence,
        }


@dataclass(frozen=True)
class SpatialEntity:
    """A fused object state; ``observed`` and ``inferred`` never collapse."""

    object_id: str
    sector_index: int
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    predicted_position: tuple[float, float, float]
    confidence: float
    uncertainty_m: float
    modality_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    observed: bool
    occluded: bool
    occupied: bool

    @property
    def visibility(self) -> str:
        return "observed" if self.observed and not self.occluded else "inferred"

    def to_dict(self) -> dict[str, object]:
        return {
            "object_id": self.object_id,
            "sector_index": self.sector_index,
            "position": list(self.position),
            "velocity": list(self.velocity),
            "predicted_position": list(self.predicted_position),
            "confidence": self.confidence,
            "uncertainty_m": self.uncertainty_m,
            "modality_ids": list(self.modality_ids),
            "source_ids": list(self.source_ids),
            "observed": self.observed,
            "visibility": self.visibility,
            "occluded": self.occluded,
            "occupied": self.occupied,
        }


@dataclass(frozen=True)
class SpatialWorldSnapshot:
    """Immutable 4D world model output consumed by safety/reference code."""

    timestamp_ns: int
    calibration_id: str
    region_id: str
    mode: str
    sector_count: int
    status: str
    confidence: float
    covered_sectors: tuple[int, ...]
    unknown_sectors: tuple[int, ...]
    entities: tuple[SpatialEntity, ...]
    modality_ids: tuple[str, ...]
    emission_modalities: tuple[str, ...]
    reasons: tuple[str, ...]
    conflict: bool
    stop_required: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp_ns": self.timestamp_ns,
            "calibration_id": self.calibration_id,
            "region_id": self.region_id,
            "mode": self.mode,
            "sector_count": self.sector_count,
            "status": self.status,
            "confidence": self.confidence,
            "covered_sectors": list(self.covered_sectors),
            "unknown_sectors": list(self.unknown_sectors),
            "coverage_fraction": len(self.covered_sectors) / self.sector_count,
            "entities": [entity.to_dict() for entity in self.entities],
            "modality_ids": list(self.modality_ids),
            "emission_modalities": list(self.emission_modalities),
            "reasons": list(self.reasons),
            "conflict": self.conflict,
            "stop_required": self.stop_required,
            "simulation_only": True,
        }

    def to_safety_snapshot(self) -> SpatialSnapshot:
        """Adapt the rich world model to the legacy movement safety contract."""
        return SpatialSnapshot(
            timestamp_ns=self.timestamp_ns,
            calibration_id=self.calibration_id,
            region_id=self.region_id,
            status=self.status,
            confidence=self.confidence,
            modality_ids=self.modality_ids,
            conflict=self.conflict,
            stop_required=self.stop_required,
            reasons=self.reasons,
        )


class SpatialRecognitionSystem:
    """Fuse bounded measurements with passive-first, fail-closed semantics."""

    def __init__(
        self,
        *,
        sector_count: int = 16,
        max_age_ns: int = 100_000_000,
        min_confidence: float = 0.75,
        prediction_horizon_s: float = 1.0,
        mode: str = "normal",
        min_independent_modalities: int = 2,
        require_wave_evidence: bool = True,
    ) -> None:
        if sector_count < 1 or max_age_ns < 1:
            raise ValueError("sector_count and max_age_ns must be positive")
        if not 0.0 < min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        if prediction_horizon_s < 0.0 or prediction_horizon_s > 60.0:
            raise ValueError("prediction_horizon_s must be between 0 and 60")
        if mode not in MODE_ACTIVE_MODALITIES:
            raise ValueError("unsupported spatial operating mode")
        if min_independent_modalities < 1:
            raise ValueError("min_independent_modalities must be positive")
        self.sector_count = sector_count
        self.max_age_ns = max_age_ns
        self.min_confidence = min_confidence
        self.prediction_horizon_s = float(prediction_horizon_s)
        self.mode = mode
        self.min_independent_modalities = min_independent_modalities
        self.require_wave_evidence = require_wave_evidence

    def fuse(
        self,
        measurements: Iterable[SpatialMeasurement],
        *,
        now_ns: int,
        calibration_id: str,
        region_id: str,
        mode: str | None = None,
    ) -> SpatialWorldSnapshot:
        if now_ns < 0 or not calibration_id or not region_id:
            raise ValueError("timestamp, calibration, and region are required")
        selected_mode = mode or self.mode
        if selected_mode not in MODE_ACTIVE_MODALITIES:
            raise ValueError("unsupported spatial operating mode")

        reasons: list[str] = []
        valid: list[SpatialMeasurement] = []
        for measurement in measurements:
            if measurement.region_id != region_id:
                reasons.append("region_mismatch")
                continue
            if measurement.calibration_id != calibration_id:
                reasons.append("calibration_mismatch")
                continue
            if measurement.sector_index >= self.sector_count:
                reasons.append("sector_out_of_range")
                continue
            if measurement.timestamp_ns > now_ns:
                reasons.append("future_measurement")
                continue
            if now_ns - measurement.timestamp_ns > self.max_age_ns:
                reasons.append("stale_measurement")
                continue
            if not measurement.healthy:
                reasons.append(f"unhealthy_source:{measurement.source_id}")
                continue
            if measurement.emits_energy and measurement.modality not in MODE_ACTIVE_MODALITIES[selected_mode]:
                reasons.append(f"active_modality_disabled:{measurement.modality}")
                continue
            valid.append(measurement)

        all_sectors = set(range(self.sector_count))
        covered = {item.sector_index for item in valid}
        unknown = all_sectors - covered
        if unknown:
            reasons.append("incomplete_360_coverage")

        grouped: dict[str, list[SpatialMeasurement]] = {}
        for item in valid:
            grouped.setdefault(item.object_id, []).append(item)

        entities: list[SpatialEntity] = []
        conflict = False
        for object_id, items in sorted(grouped.items()):
            occupied = [item for item in items if item.occupied]
            clear = [item for item in items if not item.occupied]
            high_occupied = max((item.confidence for item in occupied), default=0.0)
            high_clear = max((item.confidence for item in clear), default=0.0)
            if high_occupied >= self.min_confidence and high_clear >= self.min_confidence:
                conflict = True
                reasons.append(f"contradictory_evidence:{object_id}")

            total = sum(item.confidence for item in items) or 1.0
            position = tuple(
                sum(item.position[index] * item.confidence for item in items) / total
                for index in range(3)
            )
            velocity = tuple(
                sum(item.velocity[index] * item.confidence for item in items) / total
                for index in range(3)
            )
            confidence = min(item.confidence for item in items)
            predicted = tuple(
                position[index] + velocity[index] * self.prediction_horizon_s
                for index in range(3)
            )
            entities.append(
                SpatialEntity(
                    object_id=object_id,
                    sector_index=items[0].sector_index,
                    position=position,
                    velocity=velocity,
                    predicted_position=predicted,
                    confidence=confidence,
                    uncertainty_m=round(max(0.0, 1.0 - confidence), 6),
                    modality_ids=tuple(sorted({item.modality for item in items})),
                    source_ids=tuple(sorted({item.source_id for item in items})),
                    observed=any(item.observed and not item.occluded for item in items),
                    occluded=all(item.occluded for item in items),
                    occupied=any(item.occupied for item in items),
                )
            )

        occupied_entities = [item for item in entities if item.occupied]
        modality_ids = tuple(sorted({item.modality for item in valid}))
        emission_modalities = tuple(sorted({item.modality for item in valid if item.emits_energy}))
        confidence = min((item.confidence for item in valid), default=0.0)
        if len(modality_ids) < self.min_independent_modalities:
            reasons.append("insufficient_independent_modalities")
        if self.require_wave_evidence and not set(modality_ids) & WAVE_MODALITIES:
            reasons.append("wave_evidence_required")
        if not valid:
            status = "unknown"
            reasons.append("no_fresh_healthy_spatial_evidence")
        elif conflict or unknown or reasons:
            status = "unknown"
        elif occupied_entities:
            status = "occupied"
        else:
            status = "clear"

        return SpatialWorldSnapshot(
            timestamp_ns=now_ns,
            calibration_id=calibration_id,
            region_id=region_id,
            mode=selected_mode,
            sector_count=self.sector_count,
            status=status,
            confidence=confidence,
            covered_sectors=tuple(sorted(covered)),
            unknown_sectors=tuple(sorted(unknown)),
            entities=tuple(entities),
            modality_ids=modality_ids,
            emission_modalities=emission_modalities,
            reasons=tuple(dict.fromkeys(reasons)),
            conflict=conflict,
            stop_required=status != "clear" or conflict,
        )

    def demo_measurements(self, *, timestamp_ns: int = 1_000, calibration_id: str = "demo-cal") -> tuple[SpatialMeasurement, ...]:
        """Create a deterministic full-coverage scene for local replay/CLI use."""
        measurements: list[SpatialMeasurement] = []
        occupied_sectors = {3, 10}
        for sector in range(self.sector_count):
            if sector in occupied_sectors:
                continue
            measurements.append(
                SpatialMeasurement(
                    source_id=f"rgb-{sector}", modality="rgb", region_id="demo",
                    sector_index=sector, timestamp_ns=timestamp_ns,
                    calibration_id=calibration_id, object_id=f"clear-{sector}",
                    position=(float(sector), 0.0, 1.0), velocity=(0.0, 0.0, 0.0),
                    confidence=0.92, occupied=False,
                )
            )
        measurements.extend(
            [
                SpatialMeasurement(
                    source_id="rgb-person-3", modality="rgb", region_id="demo", sector_index=3,
                    timestamp_ns=timestamp_ns, calibration_id=calibration_id, object_id="person-3",
                    position=(3.0, 1.0, 1.4), velocity=(0.4, 0.0, 0.0), confidence=0.91,
                    occupied=True,
                ),
                SpatialMeasurement(
                    source_id="radar-person-3", modality="mmwave_radar", region_id="demo", sector_index=3,
                    timestamp_ns=timestamp_ns, calibration_id=calibration_id, object_id="person-3",
                    position=(3.1, 1.0, 1.4), velocity=(0.5, 0.0, 0.0), confidence=0.88,
                    occupied=True, emits_energy=True,
                ),
                SpatialMeasurement(
                    source_id="radar-occluded-10", modality="mmwave_radar", region_id="demo", sector_index=10,
                    timestamp_ns=timestamp_ns, calibration_id=calibration_id, object_id="occluded-target-10",
                    position=(10.0, -1.0, 1.0), velocity=(0.0, 0.3, 0.0), confidence=0.79,
                    occupied=True, observed=False, occluded=True, emits_energy=True,
                ),
            ]
        )
        return tuple(measurements)
