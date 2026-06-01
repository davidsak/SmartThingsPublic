#!/usr/bin/env python3
"""
generate_art.py — reproducible gothic ("Ashen Vigil") pixel-art generator.

Produces real PNG sprite sheets + layered parallax backdrops in a
Blasphemous-inspired palette: deep blue-black cathedral, crimson banners,
candle-gold accents, moonlit spires. Everything is drawn from code with Pillow
so the art is regenerable and version-controllable; it is meant as a strong
atmospheric base you can later replace piece by piece with hand-drawn art.

    cd NeonCitadel/Art
    pip3 install Pillow
    python3 generate_art.py            # writes PNGs into ./out and syncs them
                                       # into the iOS asset catalog + web playtest

Outputs (in ./out, low-res source pixels — the engines scale with nearest):
    player.png       6-frame sheet (idle x2, run x3, jump) 16x24 each
    boss.png         large armored sentinel, 64x80
    enemy.png        2-frame wretch, 16x18
    tiles.png        stone / edge / pillar tiles, 16x16 each
    pickup.png       relic (double-jump) 12x12
    bg_sky.png       moon + sky gradient (far)
    bg_spires.png    silhouetted cathedral spires (mid-far)
    bg_window.png    glowing rose window + arches (mid)
    bg_pillars.png   foreground pillars/railing (near)
"""

from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

random.seed(7)  # deterministic art

# ---------------------------------------------------------------- palette ----
# Blasphemous-leaning gothic palette (RGBA).
P = {
    "void":        (8, 10, 22, 255),
    "nightA":      (14, 18, 42, 255),
    "nightB":      (26, 30, 66, 255),
    "moon":        (208, 224, 255, 255),
    "moonGlow":    (120, 150, 220, 255),
    "stoneDark":   (28, 26, 48, 255),
    "stone":       (44, 42, 74, 255),
    "stoneLite":   (70, 66, 110, 255),
    "stoneEdge":   (96, 90, 150, 255),
    "crimson":     (150, 24, 40, 255),
    "crimsonLite": (206, 44, 60, 255),
    "gold":        (224, 176, 72, 255),
    "goldLite":    (255, 224, 138, 255),
    "candle":      (255, 196, 110, 255),
    "rose":        (224, 64, 120, 255),
    "roseLite":    (255, 150, 196, 255),
    "glass1":      (90, 150, 230, 255),
    "glass2":      (230, 96, 120, 255),
    "glass3":      (240, 200, 110, 255),
    "flesh":       (208, 168, 140, 255),
    "fleshDark":   (150, 110, 92, 255),
    "robe":        (140, 30, 36, 255),   # penitent crimson robe
    "robeDark":    (92, 18, 26, 255),
    "hood":        (40, 18, 24, 255),
    "steel":       (150, 156, 178, 255),
    "steelDark":   (84, 90, 116, 255),
    "steelLite":   (198, 204, 224, 255),
    "bone":        (224, 214, 188, 255),
    "clear":       (0, 0, 0, 0),
}


def img(w, h):
    return Image.new("RGBA", (w, h), P["clear"])


def save(im: Image.Image, name: str):
    path = OUT / name
    im.save(path)
    print(f"  {name:16s} {im.width}x{im.height}")
    return path


# --------------------------------------------------------- grid sprites ----
def from_grid(grid, legend, cell=1):
    """Build an image from a list of equal-length strings."""
    h = len(grid)
    w = max(len(r) for r in grid)
    im = img(w * cell, h * cell)
    px = im.load()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            col = legend.get(ch)
            if not col:
                continue
            for dy in range(cell):
                for dx in range(cell):
                    px[x * cell + dx, y * cell + dy] = col
    return im


def shade_rect(d, x0, y0, x1, y1, base, lite, dark):
    """A stone block with top/left highlight and bottom/right shadow."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.line([x0, y0, x1, y0], fill=lite)       # top
    d.line([x0, y0, x0, y1], fill=lite)       # left
    d.line([x0, y1, x1, y1], fill=dark)       # bottom
    d.line([x1, y0, x1, y1], fill=dark)       # right


# ============================================================ characters ====
def make_player():
    """6 frames, 16x24 each: idle1, idle2, run1, run2, run3, jump.
    A hooded penitent in a crimson robe. Side-facing."""
    FW, FH, N = 16, 24, 6
    sheet = img(FW * N, FH)
    L = {
        "h": P["hood"], "r": P["robe"], "d": P["robeDark"],
        "f": P["flesh"], "g": P["gold"], "b": P["bone"], "s": P["steelLite"],
    }

    # Base penitent body (idle). '.' transparent.
    idle = [
        "................",
        "......hhhh......",
        ".....hhhhhh.....",
        ".....hffffh.....",
        ".....hffffh.....",
        "......ffff......",
        ".....rdrrdr.....",
        "....rrrrrrrr....",
        "...rrrrrrrrrr...",
        "...rdrrrrrrdr...",
        "...rdrrrrrrdr...",
        "...rrrrrrrrrr...",
        "....rrrrrrrr....",
        "....rd rrd r....".replace(" ", "."),
        "....rd.rrd.r....",
        "....dd.rrd.d....",
        ".....r.rr.r.....",
        ".....d.dd.d.....",
        ".....d.dd.d.....",
        "....dd.dd.dd....",
        "...bbb.dd.bbb...".replace("b", "d"),
        "...ddd....ddd...",
        "................",
        "................",
    ]

    def legs(frame):
        # returns 6 rows (indices 16..21) describing leg poses for run/idle
        if frame == "idle":
            return ["....d.dd.d....", "....d.dd.d....", "...dd.dd.dd...",
                    "...dd....dd...", "...ddd..ddd...", ".............."]
        if frame == "r1":
            return ["....dd.d......", "...dd..dd.....", "..dd....dd....",
                    "..d......dd...", ".dd.......d...", ".............."]
        if frame == "r2":
            return ["....d.dd.d....", "....d.dd.d....", "....d.dd.d....",
                    "...dd..dd.....", "..dd...dd.....", ".............."]
        if frame == "r3":
            return ["......d.dd....", ".....dd..dd...", "....dd....dd..",
                    "...dd......d..", "...d.......dd.", ".............."]
        if frame == "jump":
            return ["...dd.dd.dd...", "..dd..dd..dd..", ".dd...dd...d..",
                    ".d....dd......", "......dd......", ".............."]
        return [".............."] * 6

    poses = ["idle", "idle", "r1", "r2", "r3", "jump"]
    for i, pose in enumerate(poses):
        rows = idle[:16] + [r.ljust(16, ".")[:16] for r in legs(pose)] + idle[22:]
        rows = [r.ljust(16, ".")[:16] for r in rows][:FH]
        frame = from_grid(rows, L)
        # subtle arm/staff for non-jump frames: a gold staff on the right
        d = ImageDraw.Draw(frame)
        if pose != "jump":
            d.line([12, 5, 12, 19], fill=P["gold"])
            d.point((12, 4), fill=P["goldLite"])
        sheet.alpha_composite(frame, (i * FW, 0))
    return sheet


def make_enemy():
    """2-frame crawling wretch, 16x18."""
    FW, FH, N = 16, 18, 2
    sheet = img(FW * N, FH)
    L = {"r": P["robe"], "d": P["robeDark"], "f": P["fleshDark"],
         "e": P["crimsonLite"], "b": P["bone"]}
    base = [
        "................",
        ".....dddd.......",
        "....drrrrd......",
        "...drrrrrrd.....",
        "...drffffrd.....",
        "...drfeefrd.....",   # glowing eyes
        "...drffffrd.....",
        "...drrrrrrd.....",
        "..drrrrrrrrd....",
        "..drrrrrrrrd....",
        "..drrdrrdrrd....",
        ".drr.drr.rrd....".replace(" ", "."),
        ".dd..dd..dd.....",
        ".b....b...b.....".replace("b", "d"),
        "................",
        "................",
        "................",
        "................",
    ]
    f1 = from_grid([r.ljust(16, ".")[:16] for r in base], L)
    # frame 2: legs shifted
    base2 = base[:11] + [
        ".drr.drr.rrd....".replace(" ", "."),
        "..dd..dd.dd.....",
        "...d...d..d.....",
    ] + base[14:]
    f2 = from_grid([r.ljust(16, ".")[:16] for r in base2], L)
    sheet.alpha_composite(f1, (0, 0))
    sheet.alpha_composite(f2, (FW, 0))
    return sheet


def make_boss():
    """A large armored sentinel, 64x80, gold + steel + crimson cape.
    Decorative (atmosphere/boss silhouette)."""
    W, H = 64, 80
    im = img(W, H)
    d = ImageDraw.Draw(im)
    cx = W // 2

    # Crimson cape behind.
    d.polygon([(cx - 22, 26), (cx + 22, 26), (cx + 28, 76), (cx - 28, 76)],
              fill=P["robeDark"])
    d.polygon([(cx - 16, 28), (cx + 16, 28), (cx + 20, 74), (cx - 20, 74)],
              fill=P["robe"])

    # Pauldrons (gold).
    d.ellipse([cx - 30, 28, cx - 8, 48], fill=P["gold"])
    d.ellipse([cx + 8, 28, cx + 30, 48], fill=P["gold"])
    d.ellipse([cx - 27, 31, cx - 11, 45], fill=P["goldLite"])
    d.ellipse([cx + 11, 31, cx + 27, 45], fill=P["goldLite"])

    # Torso steel.
    d.rectangle([cx - 14, 34, cx + 14, 66], fill=P["steelDark"])
    d.rectangle([cx - 11, 36, cx + 11, 64], fill=P["steel"])
    # gold trim cross on chest
    d.rectangle([cx - 2, 40, cx + 2, 60], fill=P["gold"])
    d.rectangle([cx - 8, 46, cx + 8, 50], fill=P["gold"])

    # Hooded head with skull face.
    d.polygon([(cx - 12, 6), (cx + 12, 6), (cx + 10, 30), (cx - 10, 30)],
              fill=P["hood"])
    d.ellipse([cx - 7, 12, cx + 7, 28], fill=P["bone"])
    d.ellipse([cx - 5, 17, cx - 1, 22], fill=P["void"])     # eye
    d.ellipse([cx + 1, 17, cx + 5, 22], fill=P["void"])     # eye
    d.line([cx - 4, 25, cx + 4, 25], fill=P["fleshDark"])

    # Greatsword (held to the side, gold hilt).
    sx = cx + 26
    d.rectangle([sx - 2, 8, sx + 2, 70], fill=P["steelLite"])  # blade
    d.rectangle([sx - 1, 8, sx + 1, 70], fill=P["bone"])
    d.rectangle([sx - 8, 60, sx + 8, 64], fill=P["gold"])      # crossguard
    d.rectangle([sx - 2, 64, sx + 2, 74], fill=P["gold"])      # grip
    d.ellipse([sx - 4, 72, sx + 4, 78], fill=P["goldLite"])    # pommel

    # Shield (left).
    d.ellipse([cx - 34, 44, cx - 10, 74], fill=P["gold"])
    d.ellipse([cx - 31, 47, cx - 13, 71], fill=P["goldLite"])
    d.line([cx - 22, 48, cx - 22, 70], fill=P["gold"])
    d.line([cx - 30, 59, cx - 14, 59], fill=P["gold"])

    return im


def make_tiles():
    """3 tiles in a 48x16 sheet: ground stone, edge/cap stone, pillar."""
    cell = 16
    im = img(cell * 3, cell)
    d = ImageDraw.Draw(im)

    # 0: ground stone block
    shade_rect(d, 0, 0, 15, 15, P["stone"], P["stoneLite"], P["stoneDark"])
    for (x, y) in [(4, 4), (9, 6), (3, 11), (11, 12), (7, 9)]:
        d.point((x, y), fill=P["stoneDark"])
    d.line([0, 8, 15, 8], fill=P["stoneDark"])   # mortar
    d.line([8, 0, 8, 7], fill=P["stoneDark"])
    d.line([4, 9, 4, 15], fill=P["stoneDark"])

    # 1: capstone with gold edge (top of platforms)
    shade_rect(d, 16, 0, 31, 15, P["stoneLite"], P["stoneEdge"], P["stoneDark"])
    d.line([16, 0, 31, 0], fill=P["gold"])
    d.line([16, 1, 31, 1], fill=P["goldLite"])

    # 2: fluted pillar
    d.rectangle([32, 0, 47, 15], fill=P["stoneDark"])
    for x in range(34, 47, 3):
        d.line([x, 0, x, 15], fill=P["stone"])
        d.line([x + 1, 0, x + 1, 15], fill=P["stoneLite"])
    return im


def make_pickup():
    """A holy relic (double-jump): gold reliquary with rose glow, 12x12."""
    im = img(12, 12)
    d = ImageDraw.Draw(im)
    d.polygon([(6, 0), (11, 6), (6, 11), (1, 6)], fill=P["gold"])
    d.polygon([(6, 2), (9, 6), (6, 9), (3, 6)], fill=P["goldLite"])
    d.line([6, 1, 6, 10], fill=P["roseLite"])
    d.line([2, 6, 10, 6], fill=P["roseLite"])
    d.point((6, 6), fill=(255, 255, 255, 255))
    return im


# ============================================================ backgrounds ===
def _vgrad(w, h, top, bot):
    im = img(w, h)
    px = im.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(4))
        for x in range(w):
            px[x, y] = c
    return im


def make_bg_sky(w=512, h=288):
    im = _vgrad(w, h, P["void"], P["nightB"])
    d = ImageDraw.Draw(im)
    # stars
    for _ in range(140):
        x, y = random.randint(0, w - 1), random.randint(0, int(h * 0.7))
        b = random.randint(120, 220)
        d.point((x, y), fill=(b, b, 255, 255))
    # moon with glow
    mx, my, r = int(w * 0.72), int(h * 0.28), 46
    glow = img(w, h)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([mx - r * 2, my - r * 2, mx + r * 2, my + r * 2],
               fill=(*P["moonGlow"][:3], 70))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.ellipse([mx - r, my - r, mx + r, my + r], fill=P["moon"])
    d.ellipse([mx - r + 10, my - r + 6, mx + r + 10, my + r + 6],
              fill=P["nightB"])  # crescent bite
    return im


def make_bg_spires(w=512, h=288):
    """Silhouetted cathedral skyline, semi-transparent."""
    im = img(w, h)
    d = ImageDraw.Draw(im)
    col = (*P["nightA"][:3], 235)
    x = -10
    while x < w + 20:
        bw = random.randint(28, 60)
        bh = random.randint(int(h * 0.35), int(h * 0.72))
        top = h - bh
        d.rectangle([x, top, x + bw, h], fill=col)
        # spire
        sx = x + bw // 2
        d.polygon([(sx - 6, top), (sx + 6, top), (sx, top - random.randint(20, 46))],
                  fill=col)
        # windows (faint warm glow)
        for wy in range(top + 14, h - 8, 16):
            for wx in range(x + 6, x + bw - 6, 12):
                if random.random() < 0.5:
                    d.rectangle([wx, wy, wx + 3, wy + 6],
                                fill=(*P["candle"][:3], 90))
        x += bw + random.randint(2, 10)
    return im


def make_bg_window(w=512, h=288):
    """The glowing rose window + gothic arches (mid layer, the focal glow)."""
    im = img(w, h)
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, int(h * 0.42)

    # Big pointed arch frame around the window.
    d.polygon([(cx - 110, h), (cx - 110, cy - 30), (cx, cy - 150),
               (cx + 110, cy - 30), (cx + 110, h)], fill=P["stoneDark"])
    d.polygon([(cx - 96, h), (cx - 96, cy - 24), (cx, cy - 132),
               (cx + 96, cy - 24), (cx + 96, h)], fill=P["void"])

    # Rose window glow halo.
    glow = img(w, h)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=(*P["rose"][:3], 90))
    glow = glow.filter(ImageFilter.GaussianBlur(22))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)

    # Rose window: concentric rings + petals in glass colours.
    R = 78
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=P["stoneDark"])
    d.ellipse([cx - R + 5, cy - R + 5, cx + R - 5, cy + R - 5], fill=P["glass1"])
    petals = 12
    for i in range(petals):
        a = i / petals * math.tau
        px = cx + math.cos(a) * R * 0.55
        py = cy + math.sin(a) * R * 0.55
        col = [P["glass2"], P["glass3"], P["roseLite"]][i % 3]
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=col)
        d.line([cx, cy, px, py], fill=P["stoneDark"])
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=P["goldLite"])
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=P["rose"])

    # Tall lancet windows flanking, with warm light.
    for ox in (-150, 150):
        lx = cx + ox
        d.polygon([(lx - 16, h), (lx - 16, cy + 10), (lx, cy - 30),
                   (lx + 16, cy + 10), (lx + 16, h)], fill=P["stoneDark"])
        d.polygon([(lx - 11, h - 6), (lx - 11, cy + 14), (lx, cy - 18),
                   (lx + 11, cy + 14), (lx + 11, h - 6)], fill=P["glass3"])
    return im


def make_bg_pillars(w=512, h=288):
    """Foreground pillars + railing + a crimson hanging banner (near layer)."""
    im = img(w, h)
    d = ImageDraw.Draw(im)
    # two flanking pillars
    for px0 in (10, w - 58):
        d.rectangle([px0, 0, px0 + 48, h], fill=P["stoneDark"])
        for fx in range(px0 + 6, px0 + 44, 8):
            d.line([fx, 0, fx, h], fill=P["stone"])
            d.line([fx + 1, 0, fx + 1, h], fill=P["stoneLite"])
        # capital
        d.rectangle([px0 - 6, 0, px0 + 54, 16], fill=P["stone"])
        d.line([px0 - 6, 0, px0 + 54, 0], fill=P["gold"])
    # crimson banner on left pillar
    bx = 26
    d.rectangle([bx, 18, bx + 22, 150], fill=P["crimson"])
    d.rectangle([bx + 2, 20, bx + 20, 148], fill=P["crimsonLite"])
    d.polygon([(bx, 150), (bx + 11, 164), (bx + 22, 150)], fill=P["crimson"])
    d.ellipse([bx + 5, 70, bx + 17, 82], fill=P["gold"])  # emblem
    return im


# ================================================================= build ====
def build_all():
    print("Generating gothic art into ./out:")
    save(make_player(), "player.png")
    save(make_enemy(), "enemy.png")
    save(make_boss(), "boss.png")
    save(make_tiles(), "tiles.png")
    save(make_pickup(), "pickup.png")
    save(make_bg_sky(), "bg_sky.png")
    save(make_bg_spires(), "bg_spires.png")
    save(make_bg_window(), "bg_window.png")
    save(make_bg_pillars(), "bg_pillars.png")


def sync_ios():
    """Copy PNGs into the iOS asset catalog as imagesets (1x, nearest scaling
    handled in-engine)."""
    cat = HERE.parent / "NeonCitadel" / "Assets.xcassets" / "Art"
    cat.mkdir(parents=True, exist_ok=True)
    (cat / "Contents.json").write_text(json.dumps(
        {"info": {"author": "xcode", "version": 1}}, indent=2))
    count = 0
    for png in sorted(OUT.glob("*.png")):
        name = png.stem
        iset = cat / f"{name}.imageset"
        iset.mkdir(exist_ok=True)
        (iset / png.name).write_bytes(png.read_bytes())
        (iset / "Contents.json").write_text(json.dumps({
            "images": [{"idiom": "universal", "filename": png.name, "scale": "1x"}],
            "info": {"author": "xcode", "version": 1},
            "properties": {"preserves-vector-representation": False,
                           "template-rendering-intent": "original"},
        }, indent=2))
        count += 1
    print(f"Synced {count} imagesets -> {cat.relative_to(HERE.parent)}")


if __name__ == "__main__":
    build_all()
    sync_ios()
    print("Done. (Run WebPlaytest/generate_play.py to embed this art into "
          "play.html.)")
