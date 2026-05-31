//
//  Enemy.swift
//  Neon Citadel
//
//  A patrolling drone. It walks/floats between two x-bounds, reversing at the
//  edges, and damages the player on contact.
//

import SpriteKit

final class Enemy: SKSpriteNode {

    private let speed: CGFloat = 90
    private var direction: CGFloat = 1
    private var minX: CGFloat = 0
    private var maxX: CGFloat = 0

    let touchDamage = 1

    static func make(patrolWidth: CGFloat) -> Enemy {
        let frames = PixelArt.enemyFrames()
        let texture = frames[0]
        let displaySize = CGSize(width: texture.size().width * PixelArt.scale,
                                 height: texture.size().height * PixelArt.scale)
        let enemy = Enemy(texture: texture, color: .clear, size: displaySize)
        enemy.zPosition = 40
        enemy.name = "enemy"
        enemy.configurePhysics()
        enemy.addGlow()
        enemy.startHover(frames: frames)
        enemy.patrolHalfWidth = patrolWidth / 2
        return enemy
    }

    private var patrolHalfWidth: CGFloat = 100

    /// Must be called after the node is positioned in the scene.
    func anchorPatrol() {
        minX = position.x - patrolHalfWidth
        maxX = position.x + patrolHalfWidth
    }

    private func configurePhysics() {
        let body = SKPhysicsBody(rectangleOf: CGSize(width: size.width * 0.8,
                                                     height: size.height * 0.7))
        body.affectedByGravity = false
        body.allowsRotation = false
        body.categoryBitMask = PhysicsCategory.enemy
        body.collisionBitMask = PhysicsCategory.none
        body.contactTestBitMask = PhysicsCategory.player | PhysicsCategory.attack
        physicsBody = body
    }

    private func addGlow() {
        let glow = SKSpriteNode(texture: texture)
        glow.size = size
        glow.color = Palette.enemy
        glow.colorBlendFactor = 1.0
        glow.alpha = 0.4
        glow.zPosition = -1
        glow.setScale(1.3)
        glow.blendMode = .add
        addChild(glow)
    }

    private func startHover(frames: [SKTexture]) {
        guard frames.count >= 2 else { return }
        let anim = SKAction.animate(with: frames, timePerFrame: 0.2)
        run(.repeatForever(anim), withKey: "hover")
    }

    func update(deltaTime: TimeInterval) {
        position.x += direction * speed * CGFloat(deltaTime)
        if position.x >= maxX { direction = -1; face() }
        else if position.x <= minX { direction = 1; face() }
    }

    private func face() {
        xScale = direction >= 0 ? 1 : -1
    }

    func die() {
        removeAllActions()
        physicsBody = nil
        let burst = SKAction.group([.scale(to: 1.6, duration: 0.2),
                                    .fadeOut(withDuration: 0.2)])
        run(.sequence([burst, .removeFromParent()]))
    }
}
