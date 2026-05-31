# Neon Citadel

An 80s synthwave **side-scrolling metroidvania** for iOS, built with **SpriteKit + Swift**.
Pixel-art look (nearest-neighbour, neon palette, additive glow) with a modern,
buttery 60 fps engine. This is a **playable vertical slice**: one explorable area
that demonstrates the full core loop.

![style: synthwave](https://img.shields.io/badge/style-synthwave-ff42b3)
![engine: SpriteKit](https://img.shields.io/badge/engine-SpriteKit-1ce3e3)

## What's in the slice

- **Character controller** — run, jump, **double-jump** (an unlockable ability), wall-free
  ground detection via downward ray-cast (no wall-jump bug), invulnerability frames, knockback.
- **Combat** — melee slash (`✦`) that pops enemies; **stomp** enemies from above for a bounce.
- **One enemy type** — a patrolling drone that damages on contact.
- **The metroidvania loop** — grab the **double-jump core**, which both unlocks new traversal
  *and* is the "key" that opens an **ability-gated door**. Reach the portal to clear the level.
- **Camera** that follows the player and clamps to the level bounds, with screen-shake on hits.
- **HUD** — health pips, ability indicator, and banner messages.
- **Touch controls** — on-screen D-pad + jump + attack, multi-touch aware.
- **Synthwave backdrop** — gradient sky, banded "outrun" sun, perspective grid, twinkling stars.
- **Zero binary assets** — every sprite is generated in code (`PixelArt.swift`), so the project
  compiles and runs immediately. Swap in real sprite sheets later by editing that one file.

## Requirements

- **Xcode 16+** (the project uses file-system-synchronized groups, `objectVersion = 77`)
- A Mac to build; an iPhone/iPad on **iOS 16+** or the iOS Simulator to run
- Game is **landscape**-only

## Run it

```sh
open NeonCitadel/NeonCitadel.xcodeproj
```

1. Select the **NeonCitadel** scheme and a simulator (e.g. *iPhone 15*) or your device.
2. For a physical device, set your **Team** under *Signing & Capabilities* (the bundle id is
   `com.example.NeonCitadel` — change it to something unique under your team).
3. Press **⌘R**.

Tap to start, then: `◀ ▶` move · `▲` jump (tap again in mid-air after you grab the core to
double-jump) · `✦` attack.

## How to play / win

1. Head right past the drone (slash it or stomp it).
2. Drop down and grab the glowing **double-jump core**.
3. Use your new double-jump to reach the **locked gate** — it opens now that you have the ability.
4. Climb the steps beyond it to the spinning **portal** to clear the level.

## Project layout

```
NeonCitadel/
  NeonCitadel.xcodeproj/       # Xcode project (synchronized-group based)
  NeonCitadel/
    App/         AppDelegate, GameViewController   # boot + SKView host
    Scenes/      MenuScene, GameScene             # title + gameplay
    Entities/    Player, Enemy, Collectibles      # actors, pickup, door, goal
    World/       Level, LevelBuilder, Background   # ASCII level + parser + backdrop
    Systems/     Palette, PixelArt, PhysicsCategory
    UI/          HUD, TouchControls
    Info.plist
```

## Designing levels

Levels are plain ASCII grids in `World/Level.swift` (read top-to-bottom):

```
X solid   . empty   P spawn   E enemy   C ability core   D gated door   G goal   b backdrop brick
```

Edit the `map` array — every row must be the same length — and the `LevelBuilder` turns it into
physics tiles and entities. This is the seam to grow into multiple connected rooms.

## Tuning the feel

The jump/gravity numbers are intentionally kept consistent and in one place each:

- `GameScene.gravity` = `-2600 pts/s²`
- `Player.jumpVelocity` = `900`, `Player.moveSpeed` = `340`

Jump apex ≈ `jumpVelocity² / (2·gravity)` ≈ 156 pts (~5 tiles). Change one, recompute the others.

## Roadmap ideas

- Sprite-sheet art + animation states (attack, hurt, fall)
- More abilities & gates (dash, wall-climb), a connected map with backtracking
- Save/restore, multiple rooms with scene transitions, audio (music + SFX)
- Game-controller support (the input layer is already abstracted)
