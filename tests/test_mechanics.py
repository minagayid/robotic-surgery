from __future__ import annotations

import math
import unittest

from robotic_surgery.mechanics import (
    ideal_lever_force_n,
    moment_nm,
    motor_input_torque_nm,
    planar_two_link_jacobian,
    planar_two_link_static_load,
)


class MechanicsTests(unittest.TestCase):
    def test_moment_uses_cross_product_and_si_units(self) -> None:
        self.assertEqual(moment_nm((0.1, 0.0, 0.0), (0.0, 10.0, 0.0)), (0.0, 0.0, 1.0))

    def test_ideal_lever_force_matches_tau_over_perpendicular_arm(self) -> None:
        self.assertEqual(ideal_lever_force_n(8.0, 0.2), 40.0)

    def test_gear_efficiency_increases_required_motor_torque(self) -> None:
        self.assertAlmostEqual(motor_input_torque_nm(8.0, 100.0, 0.8), 0.1)

    def test_planar_jacobian_static_load_matches_virtual_work(self) -> None:
        jacobian = planar_two_link_jacobian((0.5, 0.3), (0.0, 0.0))
        result = planar_two_link_static_load((0.5, 0.3), (0.0, 0.0), (0.0, 10.0))
        self.assertEqual(jacobian, ((0.0, 0.0), (0.8, 0.3)))
        self.assertEqual(result.end_effector_xy_m, (0.8, 0.0))
        self.assertEqual(result.joint_torques_nm, (8.0, 3.0))

    def test_non_finite_and_non_physical_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            moment_nm((math.nan, 0.0, 0.0), (0.0, 0.0, 1.0))
        with self.assertRaises(ValueError):
            ideal_lever_force_n(2.0, 0.0)
        with self.assertRaises(ValueError):
            motor_input_torque_nm(1.0, 10.0, 1.1)
        with self.assertRaises(ValueError):
            planar_two_link_static_load((0.5, -0.3), (0.0, 0.0), (1.0, 0.0))


if __name__ == "__main__":
    unittest.main()
