# Neon Citadel — Headless Test Harness

A Python reference model that validates the game's **design and logic before it
ever runs on iOS**. There's no Swift toolchain or iOS Simulator on Linux, so
this harness lets us catch real problems (impossible jumps, broken ability
gates, drifting constants) in a place where they actually execute.

> **Why Python and not Swift?** The iOS game is SpriteKit + Swift, which can't
> build or run in this Linux environment. Rather than test nothing, this harness
> re-implements the *deterministic rules and math* in Python and — critically —
> **parses the real Swift source** for every shared constant and the level map,
> so the model can't silently disagree with the app. When you move to a Mac, the
> same checks can be ported to an XCTest target (see "Next step" below).

## Run it

```sh
cd NeonCitadel/TestHarness
python3 run_tests.py          # or: python3 run_tests.py -v
```

Python 3.10+ stdlib only — no `pip install`, no dependencies. Exit code is
non-zero on failure (CI-friendly).

## What it checks (26 tests)

| Suite | File | What it proves |
|-------|------|----------------|
| **Spec sync** | `tests/test_spec_sync.py` | The Swift constants parse cleanly; jump/gravity are mutually consistent; the level map is rectangular, uses only known glyphs, and has exactly one spawn/core/door/goal. |
| **Physics** | `tests/test_physics.py` | A fixed-timestep integrator reproduces the jump arc and matches the analytic apex `v²/2g`, so the in-game jump reaches the height the level assumes. |
| **Rules** | `tests/test_rules.py` | The metroidvania logic: jump budget, double-jump grant, budget refill on landing, the ability-gated door, stomp-vs-hurt, i-frames, and death. |
| **Reachability** | `tests/test_reachability.py` | A flood-fill proves the level is **winnable**, the ability core is grabbable with the base jump, and the goal is reachable **only after** the double-jump opens the gate. |

## The key idea: no hand-copied numbers

`neon_sim/spec.py` reads the actual `.swift` files:

- `Entities/Player.swift` → `moveSpeed`, `jumpVelocity`, `maxHealth`
- `Scenes/GameScene.swift` → `gravity`, stomp bounce
- `World/Level.swift` → `tileSize` and the `map` array

If you rename a constant or reshape the level, the parser fails loudly (a red
test) instead of validating against stale values. **Change a tunable in Swift,
re-run the harness, and it re-validates the new design automatically.**

## What it found on first run

This harness paid for itself immediately — on the first run it caught:

1. **A non-rectangular level map** (rows 12–15 were one character longer),
   which would put a ground tile outside the computed world width.
2. **A bypassable "gate"** — the original level let the player simply jump over
   or around the wall, so the double-jump door wasn't actually gating anything.
   The level was redesigned into a full-height wall with the door as the only
   floor-level passage, and the flood-fill now proves the goal is unreachable
   until the door opens.
3. Two of my own **over-strict test assumptions** (an unrealistic discrete-apex
   tolerance, and testing the gate via climb-height instead of the real
   barrier), which were corrected.

A mutation check (punching a reachable hole next to the door) confirms the gate
test actually fails when the barrier is broken — i.e. the test has teeth.

## Layout

```
TestHarness/
  run_tests.py            # entry point (discovers tests/)
  neon_sim/
    spec.py               # parses constants + level map from the Swift source
    physics.py            # fixed-timestep jump integrator
    rules.py              # port of Player/Door/contact gameplay logic
    level_model.py        # grid view + geometry over the ASCII level
    reachability.py       # jump-aware flood-fill (winnability + gate proof)
  tests/
    test_spec_sync.py
    test_physics.py
    test_rules.py
    test_reachability.py
```

## Scope & honesty

This is a **logic/design** harness, not a renderer or a physics engine clone. It
does **not** verify SpriteKit rendering, touch handling, animations, or the
actual Swift code paths — those still need a real device/simulator. What it does
guarantee is that the *rules and the level* are sound, which is the class of bug
that's most painful to discover by hand on-device.

## Next step (on a Mac)

The same assertions map cleanly onto an XCTest target compiled against a small
`NeonCitadelCore` module (the deterministic logic factored out of the SpriteKit
classes). That would test the *real* Swift code rather than a port. Ask and I'll
scaffold it.
