//
//  Background.swift
//  Neon Citadel
//
//  The synthwave backdrop: a vertical gradient sky, the banded "outrun" sun,
//  a horizon glow, and a perspective floor grid. Built to be pinned to the
//  camera so it always fills the screen.
//

import SpriteKit
import UIKit

enum Background {

    static func make(for size: CGSize) -> SKNode {
        let node = SKNode()
        node.zPosition = -1000

        let w = size.width
        let h = size.height
        let horizonY = -h * 0.05   // a touch below centre

        // Sky gradient.
        let sky = SKSpriteNode(texture: gradientTexture(size: size),
                               size: size)
        sky.position = .zero
        node.addChild(sky)

        // The sun, sitting on the horizon, with dark bands across its lower half.
        let sunRadius = min(w, h) * 0.28
        let sun = bandedSun(radius: sunRadius, gradientFrom: Palette.sunCore, to: Palette.sun)
        sun.position = CGPoint(x: 0, y: horizonY + sunRadius * 0.35)
        sun.zPosition = 1
        node.addChild(sun)

        // Soft horizon glow line.
        let glow = SKSpriteNode(color: Palette.sun, size: CGSize(width: w, height: 3))
        glow.position = CGPoint(x: 0, y: horizonY)
        glow.blendMode = .add
        glow.alpha = 0.8
        glow.zPosition = 2
        glow.run(.repeatForever(.sequence([.fadeAlpha(to: 0.4, duration: 1.2),
                                           .fadeAlpha(to: 0.9, duration: 1.2)])))
        node.addChild(glow)

        // Perspective grid below the horizon.
        node.addChild(perspectiveGrid(width: w, horizonY: horizonY, bottom: -h / 2))

        // A scattering of distant stars above the horizon.
        node.addChild(starField(width: w, top: h / 2, bottom: horizonY, count: 40))

        return node
    }

    // MARK: - Pieces

    private static func bandedSun(radius: CGFloat, gradientFrom top: SKColor, to bottom: SKColor) -> SKNode {
        let container = SKNode()

        let disc = SKShapeNode(circleOfRadius: radius)
        disc.fillColor = bottom
        disc.strokeColor = .clear
        disc.glowWidth = 8
        container.addChild(disc)

        // Vertical colour shift: lighter core near the top.
        let core = SKShapeNode(circleOfRadius: radius)
        core.fillTexture = gradientTexture(size: CGSize(width: radius * 2, height: radius * 2),
                                           top: top, bottom: bottom)
        core.fillColor = .white
        core.strokeColor = .clear
        container.addChild(core)

        // Dark scan bands on the lower 55%, widening downward.
        let bandColor = Palette.background
        var y = -radius * 0.05
        var thickness: CGFloat = 3
        while y > -radius {
            let band = SKShapeNode(rectOf: CGSize(width: radius * 2.2, height: thickness))
            band.fillColor = bandColor
            band.strokeColor = .clear
            band.position = CGPoint(x: 0, y: y)
            container.addChild(band)
            y -= thickness + 7
            thickness += 1.4
        }

        // Crop bands to the disc using a crop node.
        let crop = SKCropNode()
        let mask = SKShapeNode(circleOfRadius: radius)
        mask.fillColor = .white
        mask.strokeColor = .clear
        crop.maskNode = mask
        // Move existing children under the crop node.
        let children = container.children
        children.forEach { $0.removeFromParent() }
        children.forEach { crop.addChild($0) }
        container.addChild(crop)
        return container
    }

    private static func perspectiveGrid(width: CGFloat, horizonY: CGFloat, bottom: CGFloat) -> SKNode {
        let grid = SKNode()
        grid.zPosition = 0
        let path = CGMutablePath()
        let vanishing = CGPoint(x: 0, y: horizonY)

        // Vertical converging lines.
        let verticals = 14
        let spread = width * 1.4
        for i in 0...verticals {
            let t = CGFloat(i) / CGFloat(verticals)
            let xBottom = -spread / 2 + spread * t
            path.move(to: CGPoint(x: xBottom, y: bottom))
            path.addLine(to: vanishing)
        }

        // Horizontal lines, spaced so they bunch up toward the horizon.
        let horizontals = 10
        for i in 1...horizontals {
            let t = CGFloat(i) / CGFloat(horizontals)
            // ease toward horizon
            let eased = t * t
            let y = bottom + (horizonY - bottom) * eased
            path.move(to: CGPoint(x: -width, y: y))
            path.addLine(to: CGPoint(x: width, y: y))
        }

        let shape = SKShapeNode(path: path)
        shape.strokeColor = Palette.grid
        shape.lineWidth = 1
        shape.alpha = 0.45
        shape.glowWidth = 0.5
        grid.addChild(shape)
        return grid
    }

    private static func starField(width: CGFloat, top: CGFloat, bottom: CGFloat, count: Int) -> SKNode {
        let field = SKNode()
        var rng = SystemRandomNumberGenerator()
        for _ in 0..<count {
            let x = CGFloat.random(in: -width / 2...width / 2, using: &rng)
            let y = CGFloat.random(in: bottom...top, using: &rng)
            let star = SKShapeNode(circleOfRadius: CGFloat.random(in: 0.6...1.8, using: &rng))
            star.fillColor = Palette.grid.blended(with: .white, fraction: 0.5)
            star.strokeColor = .clear
            star.position = CGPoint(x: x, y: y)
            star.alpha = CGFloat.random(in: 0.3...0.9, using: &rng)
            let twinkle = SKAction.sequence([
                .fadeAlpha(to: 0.15, duration: Double.random(in: 0.8...2.0, using: &rng)),
                .fadeAlpha(to: 0.9, duration: Double.random(in: 0.8...2.0, using: &rng)),
            ])
            star.run(.repeatForever(twinkle))
            field.addChild(star)
        }
        return field
    }

    // MARK: - Gradient textures

    static func gradientTexture(size: CGSize,
                                top: SKColor = Palette.background,
                                bottom: SKColor = Palette.backgroundNear) -> SKTexture {
        let renderer = UIGraphicsImageRenderer(size: size)
        let image = renderer.image { ctx in
            let cg = ctx.cgContext
            let colors = [top.cgColor, bottom.cgColor] as CFArray
            let space = CGColorSpaceCreateDeviceRGB()
            guard let gradient = CGGradient(colorsSpace: space, colors: colors,
                                            locations: [0, 1]) else { return }
            cg.drawLinearGradient(gradient,
                                  start: CGPoint(x: 0, y: 0),
                                  end: CGPoint(x: 0, y: size.height),
                                  options: [])
        }
        return SKTexture(image: image)
    }
}
