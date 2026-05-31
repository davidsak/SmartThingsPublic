"""
reachability.py — a sound over-approximation of where the player can get to in
the tile grid, used to prove the level is winnable AND that the ability gate is
a genuine barrier.

Model (deliberately generous, so a "can't reach" result is trustworthy):

  State = (col, row, up_budget) where up_budget is how many more tiles the
  player may still ascend before needing to touch ground again.

  - "Grounded" (solid tile directly below) refills up_budget to `max_jump_tiles`.
  - Horizontal move to a non-solid neighbour keeps the budget.
  - Upward move costs one budget (only allowed while budget > 0).
  - Downward move (gravity / falling) is always allowed into non-solid space.

Because the model lets the player move freely within the jump envelope, if it
reports the goal as UNREACHABLE the real game certainly cannot reach it either —
which is exactly the guarantee we want for the gate test.
"""

from __future__ import annotations

from collections import deque

from .level_model import Grid


def _passable(grid: Grid, col: int, row: int, blocked: tuple[int, int] | None) -> bool:
    if col < 0 or col >= grid.width or row < 0 or row >= grid.height:
        return False
    # The door cell ('D' in the grid) is non-solid floor, but when the door is
    # CLOSED it acts as a physics barrier — model that by blocking it.
    if blocked is not None and (col, row) == blocked:
        return False
    return not grid.is_solid(col, row)


def reachable_cells(grid: Grid,
                    start: tuple[int, int],
                    max_jump_tiles: int,
                    door_cell: tuple[int, int] | None = None,
                    door_open: bool = False) -> set[tuple[int, int]]:
    """Return the set of (col, row) cells reachable from `start`.

    `door_cell` is the door's grid cell. When `door_open` is False it is treated
    as an impassable barrier (matching the closed door's physics body); when
    True it is ordinary passable floor.
    """
    blocked = door_cell if (door_cell is not None and not door_open) else None

    def passable(c, r):
        return _passable(grid, c, r, blocked)

    def grounded(c, r):
        # Standing on a solid tile, or on the door sill if the door is closed
        # (the door itself is a solid barrier you can stand beside, but the
        # floor row below the play area is the real ground).
        return grid.is_solid(c, r + 1) or (r + 1 >= grid.height)

    sc, sr = start
    start_budget = max_jump_tiles if grounded(sc, sr) else 0
    best: dict[tuple[int, int], int] = {(sc, sr): start_budget}
    q: deque[tuple[int, int, int]] = deque([(sc, sr, start_budget)])
    visited: set[tuple[int, int]] = set()

    while q:
        c, r, budget = q.popleft()
        if grounded(c, r):
            budget = max_jump_tiles
        visited.add((c, r))

        moves = []
        # Horizontal
        moves.append((c - 1, r, budget))
        moves.append((c + 1, r, budget))
        # Down (fall) — gravity is free
        moves.append((c, r + 1, budget))
        # Up (jump) — only with budget
        if budget > 0:
            moves.append((c, r - 1, budget - 1))

        for nc, nr, nb in moves:
            if not passable(nc, nr):
                continue
            # Landing refills; recompute so we don't under-count.
            eff = max_jump_tiles if grounded(nc, nr) else nb
            prev = best.get((nc, nr), -1)
            if eff > prev:
                best[(nc, nr)] = eff
                q.append((nc, nr, eff))

    return visited


def can_reach(grid: Grid,
              start: tuple[int, int],
              goal: tuple[int, int],
              max_jump_tiles: int,
              door_cell: tuple[int, int] | None = None,
              door_open: bool = False) -> bool:
    return goal in reachable_cells(grid, start, max_jump_tiles,
                                   door_cell, door_open)
