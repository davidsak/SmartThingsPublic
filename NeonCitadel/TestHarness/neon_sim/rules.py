"""
rules.py — a faithful port of Neon Citadel's *gameplay rules* (not its
rendering or physics). Mirrors the decision logic in Player.swift and the
contact handling in GameScene.swift so we can unit-test the metroidvania loop:

  - jump budget and how the double-jump ability changes it
  - the budget resetting on landing
  - the ability-gated door refusing to open without the ability
  - stomp vs. side-contact damage, invulnerability, and death

Keep this aligned with the Swift. Where a number is involved it comes from
spec.load_spec(); only the branching logic is reproduced here.
"""

from __future__ import annotations

from .spec import GameSpec


class Player:
    """Mirror of Player.swift's jump/health/ability state machine."""

    def __init__(self, spec: GameSpec):
        self.spec = spec
        self.max_health = spec.max_health
        self.health = spec.max_health
        self.has_double_jump = False
        self.jumps_remaining = 0
        self.on_ground = False
        self.invulnerable = False

    # --- grounding (GameScene.updateGrounded -> Player.setGrounded) ---
    def set_grounded(self, grounded: bool) -> None:
        if grounded and not self.on_ground:
            # Landing refills the jump budget.
            self.jumps_remaining = 2 if self.has_double_jump else 1
        self.on_ground = grounded

    # --- jump (Player.jump) ---
    def jump(self) -> bool:
        """Returns True if a jump actually fired."""
        if self.on_ground:
            self.jumps_remaining = 2 if self.has_double_jump else 1
        if self.jumps_remaining <= 0:
            return False
        self.jumps_remaining -= 1
        self.on_ground = False
        return True

    # --- ability pickup (Player.grantDoubleJump) ---
    def grant_double_jump(self) -> None:
        self.has_double_jump = True
        self.jumps_remaining = max(self.jumps_remaining, 1)

    # --- damage (Player.takeDamage) ---
    def take_damage(self, amount: int) -> bool:
        """Returns True if damage was actually applied."""
        if self.invulnerable or self.health <= 0:
            return False
        self.health = max(0, self.health - amount)
        self.invulnerable = True
        return True

    def clear_invulnerability(self) -> None:
        self.invulnerable = False

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    @property
    def is_dead(self) -> bool:
        return self.health <= 0


class Door:
    """Mirror of AbilityDoor + GameScene.handleDoor."""

    def __init__(self):
        self.is_open = False

    def try_open(self, player: Player) -> bool:
        """The ability gate: opens only if the player has the double-jump."""
        if self.is_open:
            return True
        if player.has_double_jump:
            self.is_open = True
            return True
        return False


# --- enemy contact resolution (GameScene.handlePlayerEnemy) ---

def resolve_player_enemy(player: Player,
                         player_y: float,
                         player_dy: float,
                         enemy_y: float,
                         enemy_half_height: float,
                         touch_damage: int = 1) -> str:
    """Returns one of: 'stomp', 'hurt', 'ignored'.

    Stomp requires the player to be descending AND clearly above the enemy,
    matching the Swift guard exactly.
    """
    stomping = player_dy < 0 and player_y > enemy_y + enemy_half_height * 0.2
    if stomping:
        return "stomp"
    if player.take_damage(touch_damage):
        return "hurt"
    return "ignored"
