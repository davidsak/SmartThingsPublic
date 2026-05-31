//
//  Palette.swift
//  Neon Citadel
//
//  A tight 80s "outrun / synthwave" colour palette. Keeping colours in one
//  place makes it trivial to re-skin the whole game later.
//

import SpriteKit

enum Palette {
    static let background      = SKColor(red: 0.043, green: 0.024, blue: 0.094, alpha: 1.0) // deep indigo
    static let backgroundFar   = SKColor(red: 0.090, green: 0.039, blue: 0.180, alpha: 1.0)
    static let backgroundNear  = SKColor(red: 0.149, green: 0.063, blue: 0.290, alpha: 1.0)

    static let sun            = SKColor(red: 1.000, green: 0.412, blue: 0.706, alpha: 1.0) // hot pink
    static let sunCore        = SKColor(red: 1.000, green: 0.776, blue: 0.298, alpha: 1.0) // amber

    static let grid           = SKColor(red: 0.176, green: 0.890, blue: 0.890, alpha: 1.0) // cyan

    static let tile           = SKColor(red: 0.121, green: 0.094, blue: 0.255, alpha: 1.0)
    static let tileEdge       = SKColor(red: 0.451, green: 0.227, blue: 0.831, alpha: 1.0) // violet neon
    static let tileHighlight  = SKColor(red: 0.176, green: 0.890, blue: 0.890, alpha: 1.0)

    static let player         = SKColor(red: 0.286, green: 0.949, blue: 0.792, alpha: 1.0) // mint
    static let playerDark     = SKColor(red: 0.110, green: 0.494, blue: 0.451, alpha: 1.0)
    static let playerVisor    = SKColor(red: 1.000, green: 0.298, blue: 0.541, alpha: 1.0)

    static let enemy          = SKColor(red: 1.000, green: 0.271, blue: 0.341, alpha: 1.0) // red
    static let enemyDark      = SKColor(red: 0.541, green: 0.110, blue: 0.169, alpha: 1.0)
    static let enemyEye       = SKColor(red: 1.000, green: 0.898, blue: 0.400, alpha: 1.0)

    static let pickup         = SKColor(red: 1.000, green: 0.776, blue: 0.298, alpha: 1.0)
    static let door           = SKColor(red: 0.451, green: 0.227, blue: 0.831, alpha: 1.0)
    static let doorLock       = SKColor(red: 1.000, green: 0.412, blue: 0.706, alpha: 1.0)

    static let health         = SKColor(red: 1.000, green: 0.271, blue: 0.451, alpha: 1.0)
    static let healthEmpty    = SKColor(red: 0.235, green: 0.118, blue: 0.290, alpha: 1.0)

    static let uiText         = SKColor(red: 0.176, green: 0.890, blue: 0.890, alpha: 1.0)
    static let uiButton       = SKColor(red: 1.000, green: 1.000, blue: 1.000, alpha: 0.10)
    static let uiButtonStroke = SKColor(red: 0.176, green: 0.890, blue: 0.890, alpha: 0.85)
}
