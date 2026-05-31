"""
Physics tests: the discrete jump integration reproduces the analytic arc the
constants imply. This validates that the in-game jump will reach the height the
level design assumes.
"""

import unittest

from neon_sim import spec
from neon_sim.physics import simulate_jump


class TestJumpArc(unittest.TestCase):
    def setUp(self):
        self.spec = spec.load_spec()
        self.result = simulate_jump(self.spec.jump_velocity,
                                    self.spec.gravity_magnitude)

    def test_simulated_apex_matches_analytic(self):
        analytic = self.spec.jump_apex_points
        measured = self.result.apex_height
        # The discrete integrator samples the peak at frame boundaries, so the
        # observed apex sits a fraction of a step *below* the continuous value.
        # At 60fps that's a ~5% shortfall; allow 8% and require it not overshoot.
        self.assertLessEqual(measured, analytic + 1e-6,
                             "discrete apex should not exceed the analytic apex")
        self.assertAlmostEqual(measured, analytic, delta=analytic * 0.08,
                               msg=f"measured apex {measured:.1f} vs "
                                   f"analytic {analytic:.1f}")

    def test_player_actually_leaves_the_ground(self):
        self.assertGreater(self.result.apex_height, self.spec.tile_size,
                           "a jump should clear at least one tile")

    def test_air_time_is_reasonable(self):
        # Snappy arcade jump: airborne well under a second and a half.
        self.assertTrue(0.4 <= self.result.air_time <= 1.5,
                        f"air time {self.result.air_time:.2f}s out of range")

    def test_time_to_apex_symmetry(self):
        # For constant gravity, ascent ~= half the total air time.
        self.assertAlmostEqual(self.result.time_to_apex,
                               self.result.air_time / 2,
                               delta=0.05)


if __name__ == "__main__":
    unittest.main()
