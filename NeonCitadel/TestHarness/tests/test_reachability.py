"""
Reachability tests: prove the authored level is actually winnable given the
parsed movement constants — and, crucially, that the ability gate is a *real*
gate: the goal must be reachable ONLY after the double-jump opens the door.

These use a sound over-approximating flood-fill (neon_sim.reachability): it is
generous about where the player can move within the jump envelope, so an
"unreachable" verdict is a trustworthy lower bound on difficulty.
"""

import unittest

from neon_sim import spec
from neon_sim.physics import simulate_jump
from neon_sim.level_model import build_grid
from neon_sim import reachability


def _single_jump_tiles(s) -> int:
    apex = simulate_jump(s.jump_velocity, s.gravity_magnitude).apex_height
    return int(apex // s.tile_size)


class TestReachability(unittest.TestCase):
    def setUp(self):
        self.spec = spec.load_spec()
        self.level = spec.load_level_map()
        self.grid = build_grid(self.level)

        # Standing cells (row directly above the floor) for each landmark.
        def standing(glyph):
            cell = spec.find_glyphs(self.level, glyph)[0]
            return (cell.col, cell.row)

        self.spawn = standing("P")
        self.pickup = standing("C")
        self.door_cell = standing("D")     # the door occupies a wall opening
        self.goal = standing("G")

        self.single = _single_jump_tiles(self.spec)
        self.double = self.single * 2      # ability roughly doubles ascent

    def test_pickup_reachable_from_spawn_with_single_jump(self):
        self.assertTrue(
            reachability.can_reach(self.grid, self.spawn, self.pickup,
                                   self.single, self.door_cell, door_open=False),
            "the ability core must be reachable before getting the ability")

    def test_goal_unreachable_while_gate_is_closed(self):
        # Even with the double-jump's height, the closed gate must block the goal.
        self.assertFalse(
            reachability.can_reach(self.grid, self.spawn, self.goal,
                                   self.double, self.door_cell, door_open=False),
            "goal is reachable with the gate CLOSED — the wall isn't a real barrier")

    def test_goal_reachable_once_gate_opens(self):
        self.assertTrue(
            reachability.can_reach(self.grid, self.spawn, self.goal,
                                   self.double, self.door_cell, door_open=True),
            "goal must be reachable after the double-jump opens the door")

    def test_closed_gate_seals_the_left_side(self):
        # With the gate closed, nothing right of the wall column is reachable.
        cells = reachability.reachable_cells(self.grid, self.spawn,
                                             self.double, self.door_cell,
                                             door_open=False)
        wall_col = self.door_cell[0]
        right_of_wall = [(c, r) for (c, r) in cells if c > wall_col]
        self.assertEqual(right_of_wall, [],
                         "player escaped past the wall while the gate was closed")


if __name__ == "__main__":
    unittest.main()
