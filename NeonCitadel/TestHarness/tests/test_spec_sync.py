"""
Spec-sync tests: the Python model parses the real Swift source cleanly, and the
authored level is structurally valid. If these fail, the harness is out of sync
with the app (renamed constant, malformed map, stray glyph) — fix that first.
"""

import unittest

from neon_sim import spec
from neon_sim.level_model import build_grid


class TestSpecParsing(unittest.TestCase):
    def setUp(self):
        self.spec = spec.load_spec()

    def test_constants_parse_with_sane_values(self):
        s = self.spec
        self.assertGreater(s.move_speed, 0)
        self.assertGreater(s.jump_velocity, 0)
        self.assertEqual(s.max_health, 5)
        self.assertLess(s.gravity, 0, "gravity should be negative (downward)")
        self.assertGreater(s.stomp_bounce, 0)
        self.assertGreater(s.tile_size, 0)

    def test_jump_and_gravity_are_mutually_consistent(self):
        # Apex should be a "feels good" 3-6 tiles for this slice; this guards
        # against someone changing one constant and forgetting the other.
        apex_tiles = self.spec.jump_apex_tiles
        self.assertTrue(3.0 <= apex_tiles <= 6.0,
                        f"single-jump apex is {apex_tiles:.2f} tiles; "
                        "expected 3-6 — gravity/jumpVelocity may be inconsistent")


class TestLevelStructure(unittest.TestCase):
    def setUp(self):
        self.level = spec.load_level_map()
        self.grid = build_grid(self.level)

    def test_map_is_rectangular(self):
        self.assertTrue(self.grid.is_rectangular(),
                        "all level rows must be the same length")

    def test_only_known_glyphs(self):
        used = {ch for line in self.level for ch in line}
        unknown = used - spec.KNOWN_GLYPHS
        self.assertEqual(unknown, set(),
                         f"level contains unknown glyph(s): {sorted(unknown)}")

    def test_exactly_one_spawn_pickup_door_goal(self):
        self.assertEqual(len(spec.find_glyphs(self.level, "P")), 1, "spawn count")
        self.assertEqual(len(spec.find_glyphs(self.level, "C")), 1, "ability core count")
        self.assertEqual(len(spec.find_glyphs(self.level, "D")), 1, "gated door count")
        self.assertEqual(len(spec.find_glyphs(self.level, "G")), 1, "goal count")

    def test_has_at_least_one_enemy(self):
        self.assertGreaterEqual(len(spec.find_glyphs(self.level, "E")), 1)


if __name__ == "__main__":
    unittest.main()
