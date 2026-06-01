//
//  Palette.swift
//  Ashen Vigil
//
//  A gothic "cathedral / penitent" colour palette (Blasphemous-inspired):
//  deep blue-black night, crimson banners, candle-gold accents, moonlit stone.
//  Property names are kept stable so the rest of the engine re-skins for free;
//  only the values changed when the game moved from synthwave to gothic.
//

import SpriteKit

enum Palette {
    static let background      = SKColor(red: 0.031, green: 0.039, blue: 0.086, alpha: 1.0) // void blue-black
    static let backgroundFar   = SKColor(red: 0.055, green: 0.070, blue: 0.165, alpha: 1.0) // night
    static let backgroundNear  = SKColor(red: 0.102, green: 0.102, blue: 0.180, alpha: 1.0) // dark stone

    static let sun            = SKColor(red: 0.353, green: 0.588, blue: 0.902, alpha: 1.0) // cold moon
    static let sunCore        = SKColor(red: 0.816, green: 0.878, blue: 1.000, alpha: 1.0) // moon highlight

    static let grid           = SKColor(red: 0.878, green: 0.690, blue: 0.282, alpha: 1.0) // candle gold

    static let tile           = SKColor(red: 0.173, green: 0.165, blue: 0.290, alpha: 1.0) // stone
    static let tileEdge       = SKColor(red: 0.376, green: 0.353, blue: 0.588, alpha: 1.0) // lit stone edge
    static let tileHighlight  = SKColor(red: 0.878, green: 0.690, blue: 0.282, alpha: 1.0) // gold capstone

    static let player         = SKColor(red: 0.549, green: 0.118, blue: 0.141, alpha: 1.0) // penitent robe crimson
    static let playerDark     = SKColor(red: 0.361, green: 0.071, blue: 0.102, alpha: 1.0)
    static let playerVisor    = SKColor(red: 0.816, green: 0.659, blue: 0.549, alpha: 1.0) // flesh / face

    static let enemy          = SKColor(red: 0.808, green: 0.173, blue: 0.235, alpha: 1.0) // wretch crimson
    static let enemyDark      = SKColor(red: 0.361, green: 0.071, blue: 0.102, alpha: 1.0)
    static let enemyEye       = SKColor(red: 0.902, green: 0.251, blue: 0.353, alpha: 1.0) // glowing eyes

    static let pickup         = SKColor(red: 0.878, green: 0.690, blue: 0.282, alpha: 1.0) // gold relic
    static let door           = SKColor(red: 0.878, green: 0.690, blue: 0.282, alpha: 1.0) // gilt gate
    static let doorLock       = SKColor(red: 0.808, green: 0.173, blue: 0.235, alpha: 1.0) // crimson seal

    static let health         = SKColor(red: 0.808, green: 0.173, blue: 0.235, alpha: 1.0) // crimson
    static let healthEmpty    = SKColor(red: 0.173, green: 0.165, blue: 0.290, alpha: 1.0)

    static let uiText         = SKColor(red: 0.878, green: 0.690, blue: 0.282, alpha: 1.0) // gold
    static let uiButton       = SKColor(red: 1.000, green: 1.000, blue: 1.000, alpha: 0.08)
    static let uiButtonStroke = SKColor(red: 0.878, green: 0.690, blue: 0.282, alpha: 0.85)

    // New gothic accents (additive — nothing depended on these before).
    static let crimson        = SKColor(red: 0.588, green: 0.094, blue: 0.157, alpha: 1.0)
    static let rose           = SKColor(red: 0.878, green: 0.251, blue: 0.471, alpha: 1.0)
    static let candle         = SKColor(red: 1.000, green: 0.769, blue: 0.431, alpha: 1.0)
    static let stainedGlass   = SKColor(red: 0.353, green: 0.588, blue: 0.902, alpha: 1.0)
}
