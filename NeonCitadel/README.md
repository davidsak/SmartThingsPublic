# Ashen Vigil

A gothic **side-scrolling metroidvania** for iOS, built with **SpriteKit + Swift**.
Blasphemous-inspired pixel-art look — a moonlit cathedral with a glowing rose window,
crimson banners, candle-gold accents, a hooded penitent — on a modern, buttery 60 fps engine.
This is a **playable vertical slice**: one explorable area that demonstrates the full core loop.

> Formerly "Neon Citadel" (synthwave). The folder/project/bundle id keep the old name to avoid
> resigning churn; the game, art, and titles are now gothic.

![style: gothic](https://img.shields.io/badge/style-gothic-961828)
![engine: SpriteKit](https://img.shields.io/badge/engine-SpriteKit-e0b048)

## What's in the slice

- **Character controller** — run, jump, **double-jump** (an unlockable ability), wall-free
  ground detection via downward ray-cast (no wall-jump bug), invulnerability frames, knockback.
- **Combat** — melee strike (`✦`) that fells enemies; **stomp** from above for a bounce.
- **One enemy type** — a patrolling wretch that damages on contact.
- **The metroidvania loop** — claim the **relic** (double-jump), which both unlocks new traversal
  *and* is the "key" that unseals an **ability-gated door**. Reach the portal to complete the vigil.
- **Camera** that follows the player and clamps to the level bounds, with screen-shake on hits.
- **HUD** — health pips, ability indicator, and banner messages.
- **Touch controls** — on-screen D-pad + jump + strike, multi-touch aware.
- **Gothic backdrop** — layered parallax cathedral (moon + spires + rose window + pillars),
  drifting candle embers.
- **Real generated art with procedural fallback** — sprites + backdrops are real PNGs produced by
  `Art/generate_art.py` (reproducible, version-controlled) and loaded from the asset catalog; if
  the art is absent the engine falls back to code-drawn pixels, so it always runs. Swap in
  hand-drawn art by replacing the PNGs (or editing the generator).

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

**Getting it onto your own iPhone/iPad?** See **[RUN_ON_IOS.md](RUN_ON_IOS.md)** for the
full step-by-step (free Apple ID signing, Developer Mode, trust prompt, wireless install,
and troubleshooting). No Mac handy? You can play `WebPlaytest/play.html` in Safari right now.

Tap to start, then: `◀ ▶` move · `▲` jump (tap again in mid-air after you grab the core to
double-jump) · `✦` attack.

## How to play / win

A full-height wall splits the level; the only way across is the **gated door**,
which won't open until you have the double-jump.

1. From spawn, deal with the patrolling drone (slash it or stomp it from above).
2. Jump up to grab the glowing **double-jump core** on your side of the wall.
3. Head to the **gated door** at floor level — it unlocks now that you have the ability.
4. Pass through to the spinning **portal** on the far side to clear the level.

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
    Assets.xcassets/Art/         # generated PNG sprite sheets + backdrops
  Art/                         # reproducible art generator (Pillow) + ./out PNGs
  TestHarness/                 # headless Python test harness (runs on any OS)
  WebPlaytest/                 # self-contained browser port (play.html)
```

## Art pipeline

The gothic art is **generated and reproducible**, not committed by hand alone:

```sh
cd Art && pip3 install Pillow && python3 generate_art.py   # writes ./out/*.png
                                                           # + syncs the asset catalog
cd ../WebPlaytest && python3 generate_play.py              # embeds art into play.html
```

`Art/generate_art.py` draws every sprite sheet (penitent, wretch, boss sentinel, tiles,
relic) and the four parallax backdrop layers (sky/moon, spires, rose window, pillars) with
Pillow, then copies them into `NeonCitadel/Assets.xcassets/Art/` as imagesets. The Swift
engine (`PixelArt.loadTexture`/`sliceSheet`) loads these PNGs and **falls back to code-drawn
pixels** if they're missing, so the project always runs. To use hand-drawn art, drop
replacement PNGs into the asset catalog (same names) or edit the generator.

## Testing without a Mac

Because the game can't build on non-Apple platforms, there's a **headless Python
test harness** under `TestHarness/` that validates the game's *logic and design*
— jump physics, the double-jump ability rules, and a flood-fill proof that the
level is winnable and the ability gate is a real barrier. It parses the actual
Swift source for every shared constant, so it can't drift from the app.

```sh
cd TestHarness && python3 run_tests.py
```

No dependencies (Python 3.10+ stdlib). See `TestHarness/README.md` for details.
This complements — but does not replace — running the real app in Xcode.

## Designing levels

Levels are plain ASCII grids in `World/Level.swift` (read top-to-bottom):

```
X solid   . empty   P spawn   E enemy   C ability core   D gated door   G goal   b backdrop brick
```

Edit the `map` array — every row must be the same length — and the `LevelBuilder` turns it into
physics tiles and entities. This is the seam to grow into multiple connected rooms.

After editing the level or any tunable, run the **headless test harness** to confirm the level is
still winnable and the ability gate still gates (see `TestHarness/README.md`):

```sh
cd TestHarness && python3 run_tests.py
```

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
