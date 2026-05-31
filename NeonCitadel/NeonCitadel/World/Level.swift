//
//  Level.swift
//  Neon Citadel
//
//  The level is authored as an ASCII grid (read top-to-bottom) and turned into
//  physics tiles + entities by `LevelBuilder`. This makes level design a matter
//  of editing text, and is easy to extend into multiple rooms later.
//
//  Legend:
//    X  solid tile          .  empty
//    P  player spawn        E  enemy patrol point
//    C  ability core        D  ability-gated door
//    G  goal / exit         b  background brick (decoration, non-solid)
//

import SpriteKit

enum Level {

    /// Display size of one tile, in points.
    static let tileSize: CGFloat = 32

    /// Vertical slice layout. Every row must be the same length.
    ///
    /// The wall in column 25 (rows 1–11) is a true barrier: the only way to the
    /// right-hand side — and the goal — is through the door 'D' at floor level,
    /// which requires the double-jump ability. The ability core 'C' sits on the
    /// left side, reachable with the base single jump.
    static let map: [String] = [
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        ".........................X........................",
        "............C............X........................",
        ".........................X........................",
        "..P.....E................D...................G....",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    ]

    static var columns: Int { map.first?.count ?? 0 }
    static var rows: Int { map.count }
    static var worldWidth: CGFloat { CGFloat(columns) * tileSize }
    static var worldHeight: CGFloat { CGFloat(rows) * tileSize }

    /// Convert a (column, row-from-top) grid cell to a centre position in scene space.
    /// Scene origin is bottom-left; row 0 is the top of the map.
    static func position(col: Int, row: Int) -> CGPoint {
        let x = (CGFloat(col) + 0.5) * tileSize
        let y = (CGFloat(rows - 1 - row) + 0.5) * tileSize
        return CGPoint(x: x, y: y)
    }
}
