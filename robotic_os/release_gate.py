"""Machine-checkable release gate for the physical production boundary."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .soak import soak_report_digest


GATE_VERSION = "robotx-production-gate/v1"


@dataclass(frozen=True)
class GateCheck:
    name: str
    passed: bool
    evidence: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "evidence": self.evidence,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ReleaseGateReport:
    status: str
    production_approved: bool
    gate_version: str
    checks: tuple[GateCheck, ...]
    evidence_digest: str
    checked_at_ns: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "production_approved": self.production_approved,
            "gate_version": self.gate_version,
            "checks": [check.to_dict() for check in self.checks],
            "evidence_digest": self.evidence_digest,
            "checked_at_ns": self.checked_at_ns,
        }


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _at_least(value: Any, minimum: int) -> bool:
    try:
        return int(value) >= minimum
    except (TypeError, ValueError, OverflowError):
        return False


def evaluate_release(manifest: dict[str, Any], *, minimum_soak_iterations: int = 86_400) -> ReleaseGateReport:
    """Evaluate evidence without granting certification or clinical approval."""
    if not isinstance(manifest, dict):
        raise ValueError("release manifest must be an object")
    if minimum_soak_iterations < 1:
        raise ValueError("minimum_soak_iterations must be positive")
    target = manifest.get("target_hardware")
    def section(name: str) -> dict[str, Any]:
        value = manifest.get(name)
        return value if isinstance(value, dict) else {}

    safety = section("certified_safety_controller")
    calibration = section("calibration")
    hil = section("hardware_in_loop")
    soak = section("soak")
    checksum = str(calibration.get("checksum", "")).lower()
    checks = (
        GateCheck(
            "target_hardware_selected",
            isinstance(target, str) and bool(target.strip()) and target.lower() not in {"simulation", "tbd", "unknown"},
            "target_hardware",
            "select the exact robot, drives, sensors, and workcell",
        ),
        GateCheck(
            "certified_safety_controller",
            safety.get("certified") is True and bool(safety.get("certificate_id")),
            "certified_safety_controller",
            "provide an independently verified safety PLC/drive certificate and hazard-analysis trace",
        ),
        GateCheck(
            "calibration_evidence",
            bool(calibration.get("calibration_id")) and len(checksum) == 64 and all(char in "0123456789abcdef" for char in checksum) and bool(calibration.get("approved_by")),
            "calibration",
            "provide target-hardware calibration, checksum, expiry, and approving authority",
        ),
        GateCheck(
            "hardware_in_loop",
            hil.get("passed") is True and hil.get("independent_verification") is True,
            "hardware_in_loop",
            "run the agreed fault suite against the selected hardware with independent verification",
        ),
        GateCheck(
            "long_duration_soak",
            soak.get("status") == "pass"
            and soak.get("external_actuation") is False
            and soak.get("unexpected") == 0
            and soak.get("deterministic_inputs") is True
            and _at_least(soak.get("iterations", 0), minimum_soak_iterations)
            and _at_least(soak.get("fault_rejected", 0), 1)
            and soak.get("evidence_digest") == soak_report_digest(soak),
            "soak",
            f"run at least {minimum_soak_iterations} replayable iterations and preserve an untampered evidence digest",
        ),
        GateCheck(
            "independent_release_review",
            manifest.get("independent_review") is True,
            "independent_review",
            "obtain separate safety, quality, and operational sign-off",
        ),
    )
    passed = all(check.passed for check in checks)
    status = "eligible_for_independent_production_review" if passed else "blocked"
    payload = {
        "status": status,
        "production_approved": False,
        "gate_version": GATE_VERSION,
        "checks": [check.to_dict() for check in checks],
        "checked_at_ns": int(manifest.get("checked_at_ns", time.time_ns())),
    }
    return ReleaseGateReport(
        status=status,
        production_approved=False,
        gate_version=GATE_VERSION,
        checks=checks,
        evidence_digest=_digest(payload),
        checked_at_ns=payload["checked_at_ns"],
    )


def load_manifest(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("release manifest is missing or invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("release manifest must be an object")
    return payload
