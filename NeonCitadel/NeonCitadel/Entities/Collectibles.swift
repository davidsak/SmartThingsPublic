//
//  Collectibles.swift
//  Neon Citadel
//
//  The ability pickup (double-jump core) and the ability-gated door — the
//  defining metroidvania loop: find the power, then the world opens up.
//

import SpriteKit

final class AbilityPickup: SKSpriteNode {

    static func make() -> AbilityPickup {
        let texture = PixelArt.pickupTexture()
        let displaySize = CGSize(width: texture.size().width * PixelArt.scale,
                                 height: texture.size().height * PixelArt.scale)
        let node = AbilityPickup(texture: texture, color: .clear, size: displaySize)
        node.name = "pickup"
        node.zPosition = 45
        node.configurePhysics()
        node.addGlowAndMotion()
        return node
    }

    private func configurePhysics() {
        let body = SKPhysicsBody(circleOfRadius: size.width * 0.5)
        body.affectedByGravity = false
        body.isDynamic = false
        body.categoryBitMask = PhysicsCategory.pickup
        body.collisionBitMask = PhysicsCategory.none
        body.contactTestBitMask = PhysicsCategory.player
        physicsBody = body
    }

    private func addGlowAndMotion() {
        let glow = SKSpriteNode(texture: texture)
        glow.size = size
        glow.color = Palette.pickup
        glow.colorBlendFactor = 1
        glow.alpha = 0.5
        glow.blendMode = .add
        glow.zPosition = -1
        glow.setScale(1.4)
        addChild(glow)

        let bob = SKAction.sequence([.moveBy(x: 0, y: 10, duration: 0.8),
                                     .moveBy(x: 0, y: -10, duration: 0.8)])
        bob.timingMode = .easeInEaseOut
        run(.repeatForever(bob))
        glow.run(.repeatForever(.sequence([.fadeAlpha(to: 0.2, duration: 0.8),
                                           .fadeAlpha(to: 0.6, duration: 0.8)])))
    }

    func collect(completion: @escaping () -> Void) {
        physicsBody = nil
        run(.sequence([.group([.scale(to: 2.0, duration: 0.25),
                               .fadeOut(withDuration: 0.25)]),
                       .removeFromParent(),
                       .run(completion)]))
    }
}

final class AbilityDoor: SKSpriteNode {

    private(set) var isOpen = false

    static func make(height: CGFloat) -> AbilityDoor {
        let width: CGFloat = 16 * PixelArt.scale
        let node = AbilityDoor(color: Palette.door, size: CGSize(width: width, height: height))
        node.name = "door"
        node.zPosition = 30
        node.configurePhysics()
        node.decorate()
        return node
    }

    private func configurePhysics() {
        let body = SKPhysicsBody(rectangleOf: size)
        body.isDynamic = false
        body.categoryBitMask = PhysicsCategory.door
        body.collisionBitMask = PhysicsCategory.player
        body.contactTestBitMask = PhysicsCategory.player
        physicsBody = body
    }

    private func decorate() {
        // Neon frame + lock bars.
        let frame = SKShapeNode(rect: CGRect(x: -size.width / 2, y: -size.height / 2,
                                             width: size.width, height: size.height),
                                cornerRadius: 4)
        frame.strokeColor = Palette.doorLock
        frame.lineWidth = 3
        frame.fillColor = .clear
        frame.glowWidth = 4
        addChild(frame)

        let barCount = 4
        for i in 0..<barCount {
            let bar = SKSpriteNode(color: Palette.doorLock,
                                   size: CGSize(width: size.width * 0.7, height: 5))
            let t = CGFloat(i) / CGFloat(barCount - 1)
            bar.position = CGPoint(x: 0, y: (-size.height / 2 + 20) + t * (size.height - 40))
            bar.name = "lockbar"
            addChild(bar)
        }
        run(.repeatForever(.sequence([.fadeAlpha(to: 0.7, duration: 0.7),
                                      .fadeAlpha(to: 1.0, duration: 0.7)])))
    }

    func open() {
        guard !isOpen else { return }
        isOpen = true
        physicsBody = nil
        removeAllActions()
        let unlock = SKAction.group([.moveBy(x: 0, y: size.height, duration: 0.5),
                                     .fadeOut(withDuration: 0.5)])
        unlock.timingMode = .easeIn
        run(.sequence([unlock, .removeFromParent()]))
    }
}
