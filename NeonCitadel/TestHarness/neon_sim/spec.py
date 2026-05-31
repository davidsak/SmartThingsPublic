"""
spec.py — extracts the game's source-of-truth values directly from the Swift
files so the Python reference model can never silently disagree with the app.

If a constant is renamed or a regex stops matching, parsing raises immediately;
that surfaces as a failing test rather than a stale, lying simulation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# TestHarness/neon_sim/spec.py -> repo .../NeonCitadel/NeonCitadel (source root)
SOURCE_ROOT = Path(__file__).resolve().parents[2] / "NeonCitadel"

PLAYER_SWIFT = SOURCE_ROOT / "Entities" / "Player.swift"
GAMESCENE_SWIFT = SOURCE_ROOT / "Scenes" / "GameScene.swift"
LEVEL_SWIFT = SOURCE_ROOT / "World" / "Level.swift"


class SpecParseError(RuntimeError):
    """Raised when an expected value cannot be located in the Swift source."""


def _read(path: Path) -> str:
    if not path.is_file():
        raise SpecParseError(f"expected Swift source not found: {path}")
    return path.read_text(encoding="utf-8")


def _find_float(text: str, pattern: str, label: str) -> float:
    m = re.search(pattern, text)
    if not m:
        raise SpecParseError(f"could not parse {label!r} (pattern: {pattern})")
    return float(m.group(1))


@dataclass(frozen=True)
class GameSpec:
    # Player tunables
    move_speed: float
    jump_velocity: float
    max_health: int
    # Scene tunables
    gravity: float            # signed (negative = downward), pts/s^2
    stomp_bounce: float
    # World
    tile_size: float

    @property
    def gravity_magnitude(self) -> float:
        return abs(self.gravity)

    @property
    def jump_apex_points(self) -> float:
        """Analytic apex height of a single jump: v^2 / (2|g|)."""
        return self.jump_velocity ** 2 / (2 * self.gravity_magnitude)

    @property
    def jump_apex_tiles(self) -> float:
        return self.jump_apex_points / self.tile_size


def load_spec() -> GameSpec:
    player = _read(PLAYER_SWIFT)
    scene = _read(GAMESCENE_SWIFT)
    level = _read(LEVEL_SWIFT)

    move_speed = _find_float(
        player, r"moveSpeed:\s*CGFloat\s*=\s*([0-9.]+)", "moveSpeed")
    jump_velocity = _find_float(
        player, r"jumpVelocity:\s*CGFloat\s*=\s*([0-9.]+)", "jumpVelocity")
    max_health = int(_find_float(
        player, r"maxHealth\s*=\s*([0-9]+)", "maxHealth"))

    # gravity is written as CGVector(dx: 0, dy: -2600)
    gravity = _find_float(
        scene, r"gravity\s*=\s*CGVector\(dx:\s*0,\s*dy:\s*(-?[0-9.]+)\)",
        "gravity")
    stomp_bounce = _find_float(
        scene, r"velocity\.dy\s*=\s*([0-9.]+)\s*//\s*bounce", "stomp bounce")

    tile_size = _find_float(
        level, r"tileSize:\s*CGFloat\s*=\s*([0-9.]+)", "tileSize")

    return GameSpec(
        move_speed=move_speed,
        jump_velocity=jump_velocity,
        max_health=max_health,
        gravity=gravity,
        stomp_bounce=stomp_bounce,
        tile_size=tile_size,
    )


# ---- Level map extraction -------------------------------------------------

# Glyphs the LevelBuilder understands. Kept in sync with World/Level.swift's
# documented legend and World/LevelBuilder.swift's switch statement.
KNOWN_GLYPHS = set(".XPECDGb")


def load_level_map() -> list[str]:
    """Parse the `static let map: [String] = [ ... ]` array from Level.swift."""
    text = _read(LEVEL_SWIFT)
    m = re.search(r"static let map:\s*\[String\]\s*=\s*\[(.*?)\]",
                  text, re.DOTALL)
    if not m:
        raise SpecParseError("could not locate `static let map` array in Level.swift")
    body = m.group(1)
    rows = re.findall(r'"([^"]*)"', body)
    if not rows:
        raise SpecParseError("level map array parsed but contained no string rows")
    return rows


@dataclass(frozen=True)
class Cell:
    col: int
    row: int  # row 0 = top, matching the Swift authoring order


def find_glyphs(level: list[str], glyph: str) -> list[Cell]:
    cells = []
    for r, line in enumerate(level):
        for c, ch in enumerate(line):
            if ch == glyph:
                cells.append(Cell(col=c, row=r))
    return cells
