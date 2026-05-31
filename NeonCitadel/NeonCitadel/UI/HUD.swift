//
//  HUD.swift
//  Neon Citadel
//
//  Health pips + an ability indicator + a transient banner for messages
//  ("DOUBLE JUMP ACQUIRED", "LEVEL CLEAR"). Pinned to the camera.
//

import SpriteKit

final class HUD: SKNode {

    private var pips: [SKShapeNode] = []
    private let maxHealth: Int
    private var abilityIcon: SKShapeNode?

    init(maxHealth: Int) {
        self.maxHealth = maxHealth
        super.init()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) not implemented") }

    func layout(for size: CGSize) {
        removeAllChildren()
        pips.removeAll()

        let halfW = size.width / 2
        let halfH = size.height / 2
        let top = halfH - 30
        let left = -halfW + 30

        for i in 0..<maxHealth {
            let pip = SKShapeNode(rectOf: CGSize(width: 20, height: 20), cornerRadius: 3)
            pip.position = CGPoint(x: left + CGFloat(i) * 26, y: top)
            pip.fillColor = Palette.health
            pip.strokeColor = Palette.health.blended(with: .white, fraction: 0.4)
            pip.lineWidth = 1.5
            pip.glowWidth = 2
            pip.zPosition = 1000
            addChild(pip)
            pips.append(pip)
        }

        // Ability slot (dim until unlocked).
        let icon = SKShapeNode(circleOfRadius: 12)
        icon.position = CGPoint(x: left + CGFloat(maxHealth) * 26 + 14, y: top)
        icon.fillColor = .clear
        icon.strokeColor = Palette.healthEmpty
        icon.lineWidth = 2
        icon.zPosition = 1000
        let plus = SKLabelNode(text: "⤒")
        plus.fontName = "Menlo-Bold"
        plus.fontSize = 16
        plus.fontColor = Palette.healthEmpty
        plus.verticalAlignmentMode = .center
        plus.horizontalAlignmentMode = .center
        plus.name = "abilityGlyph"
        icon.addChild(plus)
        addChild(icon)
        abilityIcon = icon
    }

    func setHealth(_ health: Int) {
        for (i, pip) in pips.enumerated() {
            let filled = i < health
            pip.fillColor = filled ? Palette.health : Palette.healthEmpty
            pip.glowWidth = filled ? 2 : 0
        }
    }

    func setAbilityUnlocked() {
        abilityIcon?.strokeColor = Palette.pickup
        abilityIcon?.glowWidth = 3
        (abilityIcon?.childNode(withName: "abilityGlyph") as? SKLabelNode)?.fontColor = Palette.pickup
        abilityIcon?.run(.sequence([.scale(to: 1.4, duration: 0.15),
                                    .scale(to: 1.0, duration: 0.15)]))
    }

    func showBanner(_ text: String, color: SKColor = Palette.uiText) {
        childNode(withName: "banner")?.removeFromParent()

        let label = SKLabelNode(text: text)
        label.name = "banner"
        label.fontName = "AvenirNextCondensed-Heavy"
        label.fontSize = 40
        label.fontColor = color
        label.verticalAlignmentMode = .center
        label.horizontalAlignmentMode = .center
        label.position = CGPoint(x: 0, y: 40)
        label.zPosition = 1100
        label.setScale(0.6)
        label.alpha = 0
        addChild(label)

        label.run(.sequence([
            .group([.fadeIn(withDuration: 0.2), .scale(to: 1.0, duration: 0.2)]),
            .wait(forDuration: 1.4),
            .group([.fadeOut(withDuration: 0.4), .moveBy(x: 0, y: 20, duration: 0.4)]),
            .removeFromParent(),
        ]))
    }
}
