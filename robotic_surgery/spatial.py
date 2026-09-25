"""Conservative multimodal spatial-evidence fusion.

Wave modalities are explicitly supported, but their output remains probabilistic
evidence. A clear snapshot is admitted only with fresh, healthy, calibrated,
independent evidence; ambiguity becomes ``unknown`` and stops orchestration.
"""

from __future__ import annotations

from typing import Iterable

from .contracts import SpatialObservation, SpatialSnapshot, WAVE_SPATIAL_MODALITIES


class SpatialFusionEngine:
    """Fuse camera and wave evidence without treating inference as ground truth."""

    def __init__(
        self,
        *,
        max_age_ns: int = 100_000_000,
        min_confidence: float = 0.75,
        conflict_confidence: float = 0.60,
        min_independent_modalities: int = 2,
        require_wave_evidence: bool = True,
    ) -> None:
        if max_age_ns < 1:
            raise ValueError("max_age_ns must be positive")
        if not 0.0 < min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        if not 0.0 < conflict_confidence <= 1.0:
            raise ValueError("conflict_confidence must be between 0 and 1")
        if min_independent_modalities < 1:
            raise ValueError("min_independent_modalities must be positive")
        self.max_age_ns = max_age_ns
        self.min_confidence = min_confidence
        self.conflict_confidence = conflict_confidence
        self.min_independent_modalities = min_independent_modalities
        self.require_wave_evidence = require_wave_evidence

    @staticmethod
    def _snapshot(
        *,
        now_ns: int,
        calibration_id: str,
        region_id: str,
        status: str,
        confidence: float,
        modality_ids: tuple[str, ...],
        reasons: list[str],
        conflict: bool = False,
        stop_required: bool = True,
    ) -> SpatialSnapshot:
        return SpatialSnapshot(
            timestamp_ns=now_ns,
            calibration_id=calibration_id,
            region_id=region_id,
            status=status,
            confidence=confidence,
            modality_ids=modality_ids,
            conflict=conflict,
            stop_required=stop_required,
            reasons=tuple(dict.fromkeys(reasons)),
        )

    def fuse(
        self,
        observations: Iterable[SpatialObservation],
        *,
        now_ns: int,
        calibration_id: str,
        region_id: str,
    ) -> SpatialSnapshot:
        if now_ns < 0:
            raise ValueError("now_ns must be non-negative")
        if not calibration_id or not region_id:
            raise ValueError("calibration_id and region_id must not be empty")

        candidates = list(observations)
        reasons: list[str] = []
        valid: list[SpatialObservation] = []
        for observation in candidates:
            if observation.calibration_id != calibration_id:
                reasons.append("calibration_mismatch")
                continue
            if observation.region_id != region_id:
                reasons.append("region_mismatch")
                continue
            if observation.timestamp_ns > now_ns:
                reasons.append("future_observation")
                continue
            if now_ns - observation.timestamp_ns > self.max_age_ns:
                reasons.append("stale_observation")
                continue
            if not observation.healthy:
                reasons.append(f"unhealthy_source:{observation.source_id}")
                continue
            valid.append(observation)

        if not valid:
            return self._snapshot(
                now_ns=now_ns,
                calibration_id=calibration_id,
                region_id=region_id,
                status="unknown",
                confidence=0.0,
                modality_ids=(),
                reasons=[*reasons, "no_fresh_healthy_spatial_evidence"],
            )

        modality_ids = tuple(sorted({observation.modality for observation in valid}))
        wave_modalities = set(modality_ids) & WAVE_SPATIAL_MODALITIES
        occupied = [item for item in valid if item.occupied]
        clear = [item for item in valid if not item.occupied]
        occupied_confidence = max((item.confidence for item in occupied), default=0.0)
        clear_confidence = min((item.confidence for item in clear), default=0.0)

        if occupied_confidence >= self.conflict_confidence and clear_confidence >= self.conflict_confidence:
            return self._snapshot(
                now_ns=now_ns,
                calibration_id=calibration_id,
                region_id=region_id,
                status="unknown",
                confidence=min(occupied_confidence, clear_confidence),
                modality_ids=modality_ids,
                reasons=[*reasons, "contradictory_spatial_evidence"],
                conflict=True,
            )

        if occupied_confidence >= self.min_confidence:
            return self._snapshot(
                now_ns=now_ns,
                calibration_id=calibration_id,
                region_id=region_id,
                status="occupied",
                confidence=occupied_confidence,
                modality_ids=modality_ids,
                reasons=[*reasons, "occupied_evidence_detected"],
            )

        independent_count = len(modality_ids)
        if independent_count < self.min_independent_modalities:
            reasons.append("insufficient_independent_modalities")
        if self.require_wave_evidence and not wave_modalities:
            reasons.append("wave_evidence_required")
        if clear_confidence < self.min_confidence:
            reasons.append("clear_confidence_below_threshold")

        if reasons:
            return self._snapshot(
                now_ns=now_ns,
                calibration_id=calibration_id,
                region_id=region_id,
                status="unknown",
                confidence=clear_confidence,
                modality_ids=modality_ids,
                reasons=reasons,
            )

        # The minimum confidence across the clear modalities avoids a strong
        # camera reading masking weak or missing wave evidence.
        return self._snapshot(
            now_ns=now_ns,
            calibration_id=calibration_id,
            region_id=region_id,
            status="clear",
            confidence=clear_confidence,
            modality_ids=modality_ids,
            reasons=[],
            stop_required=False,
        )
