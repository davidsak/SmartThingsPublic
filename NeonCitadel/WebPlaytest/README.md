# Neon Citadel — Web Playtest

**Actually play the game right now, in any browser — no Mac, no Xcode.**

The iOS build is SpriteKit + Swift and can't run on Linux. This is a faithful
**browser port** of the same game: identical physics constants, the same level,
and the same rules (run, jump, double-jump, ability gate, stomp/damage). It's for
testing *feel and design* on whatever device you're holding, ahead of the real
iOS build.

## Play it

Open **`play.html`** in any modern browser (phone or desktop). That's it — it's a
single self-contained file, no server or install needed.

- **Move:** `◀ ▶` on-screen buttons, or `A`/`D` / arrow keys
- **Jump:** `▲` button, or `W` / `↑` / `Space` (tap again in mid-air after you grab
  the core to double-jump)
- **Attack:** `✦` button, or `J` / `F`
- **Restart:** `R` (or `▲`/`Space` on the game-over / clear screen)

**Goal:** slash or stomp the drone, jump up to grab the glowing **double-jump
core**, then reach the **gated door** — it opens once you have the ability — and
step through to the **portal** on the far side.

## Why this is a legitimate playtest

`play.html` is **generated**, not hand-written. `generate_play.py` reads the same
constants and ASCII level out of the Swift source that the iOS game and the test
harness use, and bakes them in:

| Value | Source |
|-------|--------|
| `moveSpeed`, `jumpVelocity`, `maxHealth` | `NeonCitadel/Entities/Player.swift` |
| `gravity`, stomp bounce | `NeonCitadel/Scenes/GameScene.swift` |
| `tileSize` + the level `map` | `NeonCitadel/World/Level.swift` |

So the jump arcs, the gating, and the layout match the game. Change a tunable or
the level in Swift, re-run the generator, and the web playtest re-syncs.

## Regenerate after changing the game

```sh
cd NeonCitadel/WebPlaytest
python3 generate_play.py        # rewrites play.html from the Swift source
```

(Python 3.10+, stdlib only. It imports the parser from `../TestHarness`.)

## Verified winnable (headless)

The port was checked by driving its real game loop with scripted inputs in Node —
no browser, no human — performing the intended sequence (kill drone → grab core →
open gate → reach portal). It reaches **LEVEL CLEAR**. That automated playthrough
also caught a real bug during development: the door's interaction trigger was a
hair too narrow, so the gate could never be reached — now fixed.

## Honest scope

This is a **reimplementation for playtesting**, not the literal SpriteKit build.
Rendering is canvas-2D and approximates the in-game synthwave look; collision is a
straightforward AABB-vs-tile resolver rather than SpriteKit's physics engine.
Expect the *feel* to be very close, but treat the Xcode build as the ground truth
for final tuning. For pure logic/design checks, see `../TestHarness`.
