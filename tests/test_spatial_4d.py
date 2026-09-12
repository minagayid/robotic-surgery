import pytest

from robotx.spatial_4d import SpatialMeasurement, SpatialRecognitionSystem


def test_demo_has_full_coverage_and_explicit_inference():
    engine = SpatialRecognitionSystem(sector_count=16, prediction_horizon_s=2.0)
    snapshot = engine.fuse(engine.demo_measurements(), now_ns=1_000,
                           calibration_id="demo-cal", region_id="demo")
    assert snapshot.status == "occupied"
    assert snapshot.covered_sectors == tuple(range(16))
    entities = {item.object_id: item for item in snapshot.entities}
    assert entities["person-3"].visibility == "observed"
    assert entities["occluded-target-10"].visibility == "inferred"
    assert entities["occluded-target-10"].predicted_position == (10.0, -0.4, 1.0)
    assert snapshot.to_dict()["simulation_only"] is True


def test_clear_requires_independent_wave_evidence():
    engine = SpatialRecognitionSystem(sector_count=2)
    measurements = []
    for sector in range(2):
        for modality, emits in (("rgb", False), ("mmwave_radar", True)):
            measurements.append(SpatialMeasurement(
                source_id=f"{modality}-{sector}", modality=modality, region_id="demo",
                sector_index=sector, timestamp_ns=1_000, calibration_id="demo-cal",
                object_id=f"clear-{sector}", position=(0.0, 0.0, 0.0),
                velocity=(0.0, 0.0, 0.0), confidence=0.9, occupied=False,
                emits_energy=emits,
            ))
    snapshot = engine.fuse(measurements, now_ns=1_000,
                           calibration_id="demo-cal", region_id="demo")
    assert snapshot.status == "clear"
    assert not snapshot.stop_required


def test_eco_mode_disables_radar_and_missing_coverage_stops():
    engine = SpatialRecognitionSystem(sector_count=2, max_age_ns=10, mode="eco")
    measurement = SpatialMeasurement(
        source_id="radar", modality="mmwave_radar", region_id="demo", sector_index=0,
        timestamp_ns=100, calibration_id="demo-cal", object_id="target",
        position=(1.0, 0.0, 0.0), velocity=(0.0, 0.0, 0.0), confidence=0.9,
        occupied=True, emits_energy=True,
    )
    stale = SpatialMeasurement(**{**measurement.to_dict(), "source_id": "stale", "timestamp_ns": 1})
    snapshot = engine.fuse([stale, measurement], now_ns=100,
                           calibration_id="demo-cal", region_id="demo")
    assert snapshot.status == "unknown"
    assert snapshot.stop_required
    assert "active_modality_disabled:mmwave_radar" in snapshot.reasons
    assert "stale_measurement" in snapshot.reasons


def test_contradiction_is_unknown():
    engine = SpatialRecognitionSystem(sector_count=1)
    common = dict(region_id="demo", sector_index=0, timestamp_ns=1_000,
                  calibration_id="demo-cal", object_id="target",
                  position=(1.0, 0.0, 0.0), velocity=(0.0, 0.0, 0.0), confidence=0.9)
    snapshot = engine.fuse([
        SpatialMeasurement(source_id="rgb", modality="rgb", occupied=True, **common),
        SpatialMeasurement(source_id="radar", modality="mmwave_radar", occupied=False,
                           emits_energy=True, **common),
    ], now_ns=1_000, calibration_id="demo-cal", region_id="demo")
    assert snapshot.status == "unknown"
    assert snapshot.conflict
    assert "contradictory_evidence:target" in snapshot.reasons


def test_invalid_vector_is_rejected():
    with pytest.raises(ValueError):
        SpatialMeasurement(
            source_id="rgb", modality="rgb", region_id="demo", sector_index=0,
            timestamp_ns=0, calibration_id="cal", object_id="target",
            position=(1.0, 2.0), velocity=(0.0, 0.0, 0.0), confidence=0.9, occupied=False,
        )
