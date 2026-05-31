"""
Gameplay-rule tests: the metroidvania loop logic — jump budget, the double-jump
ability, the ability-gated door, and enemy contact resolution — behaves exactly
as the Swift intends.
"""

import unittest

from neon_sim import spec
from neon_sim.rules import Player, Door, resolve_player_enemy


class TestJumpBudget(unittest.TestCase):
    def setUp(self):
        self.player = Player(spec.load_spec())

    def test_single_jump_without_ability(self):
        self.player.set_grounded(True)
        self.assertTrue(self.player.jump(), "first jump should fire")
        self.assertFalse(self.player.jump(), "no double-jump without the ability")

    def test_double_jump_after_ability(self):
        self.player.set_grounded(True)
        self.player.grant_double_jump()
        self.assertTrue(self.player.jump(), "ground jump")
        self.assertTrue(self.player.jump(), "air jump granted by ability")
        self.assertFalse(self.player.jump(), "only two jumps total")

    def test_budget_refills_on_landing(self):
        self.player.set_grounded(True)
        self.player.grant_double_jump()
        self.player.jump()
        self.player.jump()
        self.assertFalse(self.player.jump())
        self.player.set_grounded(True)  # land
        self.assertTrue(self.player.jump(), "landing should refill the budget")

    def test_cannot_jump_in_air_from_fall(self):
        # Walked off a ledge (never grounded this frame) — no jump available.
        self.player.on_ground = False
        self.player.jumps_remaining = 0
        self.assertFalse(self.player.jump())


class TestAbilityGate(unittest.TestCase):
    def setUp(self):
        self.spec = spec.load_spec()

    def test_door_locked_without_ability(self):
        player = Player(self.spec)
        door = Door()
        self.assertFalse(door.try_open(player), "door must stay locked")
        self.assertFalse(door.is_open)

    def test_door_opens_with_ability(self):
        player = Player(self.spec)
        player.grant_double_jump()
        door = Door()
        self.assertTrue(door.try_open(player))
        self.assertTrue(door.is_open)

    def test_door_stays_open_once_opened(self):
        player = Player(self.spec)
        player.grant_double_jump()
        door = Door()
        door.try_open(player)
        self.assertTrue(door.try_open(player))


class TestCombatAndHealth(unittest.TestCase):
    def setUp(self):
        self.spec = spec.load_spec()

    def test_side_contact_deals_damage(self):
        p = Player(self.spec)
        outcome = resolve_player_enemy(p, player_y=100, player_dy=0,
                                       enemy_y=100, enemy_half_height=16)
        self.assertEqual(outcome, "hurt")
        self.assertEqual(p.health, self.spec.max_health - 1)

    def test_descending_from_above_is_a_stomp(self):
        p = Player(self.spec)
        outcome = resolve_player_enemy(p, player_y=140, player_dy=-200,
                                       enemy_y=100, enemy_half_height=16)
        self.assertEqual(outcome, "stomp")
        self.assertEqual(p.health, self.spec.max_health, "stomp costs no health")

    def test_invulnerability_blocks_second_hit(self):
        p = Player(self.spec)
        self.assertTrue(p.take_damage(1))
        self.assertFalse(p.take_damage(1), "i-frames should block immediate re-hit")
        self.assertEqual(p.health, self.spec.max_health - 1)

    def test_player_dies_at_zero_health(self):
        p = Player(self.spec)
        for _ in range(self.spec.max_health):
            p.take_damage(1)
            p.clear_invulnerability()
        self.assertTrue(p.is_dead)

    def test_heal_clamps_to_max(self):
        p = Player(self.spec)
        p.take_damage(2)
        p.heal(10)
        self.assertEqual(p.health, self.spec.max_health)


if __name__ == "__main__":
    unittest.main()
