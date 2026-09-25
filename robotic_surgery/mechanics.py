"""Idealized static mechanics calculations for engineering review.

All values use SI units: metres, newtons, radians, and newton-metres. Results
are analysis outputs, not actuator commands or validated safety limits. The
planar arm helper maps an end-effector force to joint torques with
``tau = J(q).T @ F`` for rigid links only; mass, gravity, inertia, friction,
compliance, and contact uncertainty are outside this model.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable


Vector2 = tuple[float, float]
Vector3 = tuple[float, float, float]


def _finite_vector(values: Iterable[float], *, size: int, name: str) -> tuple[float, ...]:
    try:
        vector = tuple(float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain {size} finite numbers") from exc
    if len(vector) != size or not all(math.isfinite(value) for value in vector):
        raise ValueError(f"{name} must contain {size} finite numbers")
    return vector


def _positive(value: float, *, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def moment_nm(moment_arm_m: Iterable[float], force_n: Iterable[float]) -> Vector3:
    """Return the 3D moment ``r x F`` in newton-metres."""
    rx, ry, rz = _finite_vector(moment_arm_m, size=3, name="moment_arm_m")
    fx, fy, fz = _finite_vector(force_n, size=3, name="force_n")
    return (ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx)


def ideal_lever_force_n(torque_nm: float, perpendicular_arm_m: float) -> float:
    """Return the force magnitude for an ideal lever: ``F = tau / r_perp``."""
    torque = float(torque_nm)
    if not math.isfinite(torque) or torque < 0.0:
        raise ValueError("torque_nm must be finite and non-negative")
    return torque / _positive(perpendicular_arm_m, name="perpendicular_arm_m")


def motor_input_torque_nm(
    output_torque_nm: float, gear_ratio: float, efficiency: float
) -> float:
    """Estimate idealized motor torque: ``tau_in = tau_out / (ratio * eta)``."""
    output = float(output_torque_nm)
    if not math.isfinite(output) or output < 0.0:
        raise ValueError("output_torque_nm must be finite and non-negative")
    ratio = _positive(gear_ratio, name="gear_ratio")
    eta = float(efficiency)
    if not math.isfinite(eta) or not 0.0 < eta <= 1.0:
        raise ValueError("efficiency must be greater than 0 and at most 1")
    return output / (ratio * eta)


def planar_two_link_jacobian(
    link_lengths_m: Iterable[float], joint_angles_rad: Iterable[float]
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the 2x2 end-effector position Jacobian for a planar 2R arm."""
    l1, l2 = _finite_vector(link_lengths_m, size=2, name="link_lengths_m")
    if l1 <= 0.0 or l2 <= 0.0:
        raise ValueError("link_lengths_m must be positive")
    q1, q2 = _finite_vector(joint_angles_rad, size=2, name="joint_angles_rad")
    q12 = q1 + q2
    return (
        (-l1 * math.sin(q1) - l2 * math.sin(q12), -l2 * math.sin(q12)),
        (l1 * math.cos(q1) + l2 * math.cos(q12), l2 * math.cos(q12)),
    )


@dataclass(frozen=True)
class PlanarStaticLoad:
    """Static planar end-effector load mapped to ideal joint torques."""

    end_effector_xy_m: Vector2
    external_force_xy_n: Vector2
    joint_torques_nm: Vector2

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def planar_two_link_static_load(
    link_lengths_m: Iterable[float],
    joint_angles_rad: Iterable[float],
    external_force_xy_n: Iterable[float],
) -> PlanarStaticLoad:
    """Compute planar forward position and static ``J.T @ F`` joint loads."""
    l1, l2 = _finite_vector(link_lengths_m, size=2, name="link_lengths_m")
    if l1 <= 0.0 or l2 <= 0.0:
        raise ValueError("link_lengths_m must be positive")
    q1, q2 = _finite_vector(joint_angles_rad, size=2, name="joint_angles_rad")
    fx, fy = _finite_vector(external_force_xy_n, size=2, name="external_force_xy_n")
    q12 = q1 + q2
    x = l1 * math.cos(q1) + l2 * math.cos(q12)
    y = l1 * math.sin(q1) + l2 * math.sin(q12)
    jacobian = planar_two_link_jacobian((l1, l2), (q1, q2))
    tau1 = jacobian[0][0] * fx + jacobian[1][0] * fy
    tau2 = jacobian[0][1] * fx + jacobian[1][1] * fy
    return PlanarStaticLoad(
        end_effector_xy_m=(x, y),
        external_force_xy_n=(fx, fy),
        joint_torques_nm=(tau1, tau2),
    )
