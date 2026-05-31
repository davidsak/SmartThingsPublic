//
//  PixelArt.swift
//  Neon Citadel
//
//  All sprite art is generated from code as small pixel grids, then rendered
//  with nearest-neighbour filtering so it scales up into crisp, chunky pixels.
//  This keeps the project asset-free and runnable out of the box. To use real
//  art later, just replace the textures returned here with SKTexture(imageNamed:).
//

import SpriteKit
import UIKit

enum PixelArt {

    /// Point size (in points) that a single source pixel occupies on screen.
    static let scale: CGFloat = 4.0

    // MARK: - Grid based generation

    /// Builds a texture from a string grid. Each character maps to a colour via
    /// `legend`; a space (or any unmapped character) is transparent.
    ///
    /// Rows are listed top-to-bottom, the way the art reads on screen.
    static func texture(grid: [String], legend: [Character: SKColor]) -> SKTexture {
        let rows = grid.count
        let cols = grid.map { $0.count }.max() ?? 0
        guard rows > 0, cols > 0 else { return SKTexture() }

        let size = CGSize(width: cols, height: rows)
        let renderer = imageRenderer(pixelSize: size)

        let image = renderer.image { ctx in
            let cg = ctx.cgContext
            for (r, line) in grid.enumerated() {
                for (c, ch) in line.enumerated() {
                    guard let color = legend[ch] else { continue }
                    cg.setFillColor(color.cgColor)
                    // Flip vertically: row 0 is the top of the art.
                    let rect = CGRect(x: c, y: rows - 1 - r, width: 1, height: 1)
                    cg.fill(rect)
                }
            }
        }

        let texture = SKTexture(image: image)
        texture.filteringMode = .nearest
        return texture
    }

    /// A solid rounded-ish tile texture with a neon edge and inner detail.
    static func tileTexture() -> SKTexture {
        let grid = [
            "EEEEEEEE",
            "EHHHHHHE",
            "EHTTTTHE",
            "EHTTTTHE",
            "EHTTTTHE",
            "EHTTTTHE",
            "EHHHHHHE",
            "EEEEEEEE",
        ]
        let legend: [Character: SKColor] = [
            "E": Palette.tileEdge,
            "H": Palette.tile.blended(with: Palette.tileHighlight, fraction: 0.18),
            "T": Palette.tile,
        ]
        return texture(grid: grid, legend: legend)
    }

    /// A faint background brick used for non-collidable backdrop walls.
    static func backTileTexture() -> SKTexture {
        let base = Palette.backgroundNear
        let grid = [
            "AAAAAAAA",
            "ABBBBBBA",
            "ABBBBBBA",
            "ABBBBBBA",
            "ABBBBBBA",
            "ABBBBBBA",
            "ABBBBBBA",
            "AAAAAAAA",
        ]
        let legend: [Character: SKColor] = [
            "A": base.blended(with: .black, fraction: 0.25),
            "B": base,
        ]
        return texture(grid: grid, legend: legend)
    }

    // MARK: - Character frames

    /// Player frames (idle + two-frame run cycle). 10x12 source pixels.
    static func playerFrames() -> [SKTexture] {
        let body = Palette.player
        let dark = Palette.playerDark
        let visor = Palette.playerVisor

        let legend: [Character: SKColor] = [
            "B": body, "D": dark, "V": visor,
        ]

        let idle = [
            "..BBBB....",
            ".BBBBBB...",
            ".BVVBBB...",
            ".BVVBBB...",
            ".BBBBBB...",
            "..BBBB....",
            ".DBBBBD...",
            "DDBBBBDD..",
            "..BB.BB...",
            "..BB.BB...",
            "..DD.DD...",
            "..DD.DD...",
        ]
        let run1 = [
            "..BBBB....",
            ".BBBBBB...",
            ".BVVBBB...",
            ".BVVBBB...",
            ".BBBBBB...",
            "..BBBB....",
            ".DBBBBD...",
            "DDBBBBDD..",
            "..BBBB....",
            ".BB..BB...",
            "DD....DD..",
            "..........",
        ]
        let run2 = [
            "..BBBB....",
            ".BBBBBB...",
            ".BVVBBB...",
            ".BVVBBB...",
            ".BBBBBB...",
            "..BBBB....",
            ".DBBBBD...",
            "DDBBBBDD..",
            "..BBBB....",
            "..BBBB....",
            "..DDDD....",
            "..DD.DD...",
        ]
        return [idle, run1, run2].map { texture(grid: $0, legend: legend) }
    }

    /// Enemy drone frames (two-frame hover). 9x8 source pixels.
    static func enemyFrames() -> [SKTexture] {
        let body = Palette.enemy
        let dark = Palette.enemyDark
        let eye = Palette.enemyEye
        let legend: [Character: SKColor] = ["B": body, "D": dark, "E": eye]

        let a = [
            "..BBBBB..",
            ".BBBBBBB.",
            "BBEBBEBBB",
            "BBEBBEBBB",
            ".BBBBBBB.",
            "..DDDDD..",
            ".D.....D.",
            "D.......D",
        ]
        let b = [
            "..BBBBB..",
            ".BBBBBBB.",
            "BBEBBEBBB",
            "BBEBBEBBB",
            ".BBBBBBB.",
            "..DDDDD..",
            "D.......D",
            ".D.....D.",
        ]
        return [a, b].map { texture(grid: $0, legend: legend) }
    }

    /// Spinning ability pickup (double-jump core). 7x7.
    static func pickupTexture() -> SKTexture {
        let c = Palette.pickup
        let h = Palette.pickup.blended(with: .white, fraction: 0.5)
        let legend: [Character: SKColor] = ["C": c, "H": h]
        let grid = [
            "...C...",
            "..CHC..",
            ".CHHHC.",
            "CHHHHHC",
            ".CHHHC.",
            "..CHC..",
            "...C...",
        ]
        return texture(grid: grid, legend: legend)
    }

    // MARK: - Helpers

    private static func imageRenderer(pixelSize: CGSize) -> UIGraphicsImageRenderer {
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1            // 1 source pixel == 1 image pixel
        format.opaque = false
        return UIGraphicsImageRenderer(size: pixelSize, format: format)
    }
}

extension SKColor {
    /// Linear blend between two colours.
    func blended(with other: SKColor, fraction: CGFloat) -> SKColor {
        var r1: CGFloat = 0, g1: CGFloat = 0, b1: CGFloat = 0, a1: CGFloat = 0
        var r2: CGFloat = 0, g2: CGFloat = 0, b2: CGFloat = 0, a2: CGFloat = 0
        getRed(&r1, green: &g1, blue: &b1, alpha: &a1)
        other.getRed(&r2, green: &g2, blue: &b2, alpha: &a2)
        let f = max(0, min(1, fraction))
        return SKColor(red: r1 + (r2 - r1) * f,
                       green: g1 + (g2 - g1) * f,
                       blue: b1 + (b2 - b1) * f,
                       alpha: a1 + (a2 - a1) * f)
    }
}
