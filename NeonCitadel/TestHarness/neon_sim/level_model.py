"""
level_model.py — a grid view over the parsed ASCII level, plus geometry helpers
used by the reachability tests. Coordinates mirror Level.swift:

  - row 0 is the TOP of the map (Swift authoring order)
  - a "solid" tile is 'X'; 'b' is non-collidable backdrop
  - "floor level" for a column is the row a standing player occupies: the empty
    row directly above the highest solid run the player would rest on.

Distances are expressed in tiles; multiply by spec.tile_size for points.
"""

from __future__ import annotations

from dataclasses import dataclass

SOLID = "X"


@dataclass(frozen=True)
class Grid:
    rows_text: list[str]

    @property
    def height(self) -> int:
        return len(self.rows_text)

    @property
    def width(self) -> int:
        return len(self.rows_text[0]) if self.rows_text else 0

    def char(self, col: int, row: int) -> str:
        if row < 0 or row >= self.height:
            return "."
        line = self.rows_text[row]
        if col < 0 or col >= len(line):
            return "."
        return line[col]

    def is_solid(self, col: int, row: int) -> bool:
        return self.char(col, row) == SOLID

    def is_rectangular(self) -> bool:
        return len({len(r) for r in self.rows_text}) == 1

    def highest_solid_row(self, col: int) -> int | None:
        """Top-most solid row in a column (smallest row index), or None."""
        for r in range(self.height):
            if self.is_solid(col, r):
                return r
        return None

    def standing_row_for(self, col: int) -> int | None:
        """Row a player stands on in this column: one above the highest solid."""
        top = self.highest_solid_row(col)
        if top is None:
            return None
        return top - 1

    def widest_floor_gap_tiles(self) -> int:
        """Widest run of columns that have NO solid tile at all (an open pit
        spanning the full height) — the hardest horizontal gap to cross."""
        widest = 0
        run = 0
        for c in range(self.width):
            if self.highest_solid_row(c) is None:
                run += 1
                widest = max(widest, run)
            else:
                run = 0
        return widest


def build_grid(rows_text: list[str]) -> Grid:
    return Grid(rows_text=rows_text)
