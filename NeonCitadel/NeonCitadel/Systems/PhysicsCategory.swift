//
//  PhysicsCategory.swift
//  Neon Citadel
//
//  Physics bitmasks for SpriteKit contact / collision filtering.
//

import Foundation

struct PhysicsCategory {
    static let none:    UInt32 = 0
    static let player:  UInt32 = 1 << 0
    static let ground:  UInt32 = 1 << 1
    static let enemy:   UInt32 = 1 << 2
    static let pickup:  UInt32 = 1 << 3
    static let door:    UInt32 = 1 << 4
    static let hazard:  UInt32 = 1 << 5
    static let attack:  UInt32 = 1 << 6
}
