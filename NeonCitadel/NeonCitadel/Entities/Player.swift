//
//  Player.swift
//  Neon Citadel
//
//  The playable character. Movement is intent-driven: the scene sets
//  `moveDirection` / calls `jump()` from the touch controls, and `update()`
//  turns that intent into velocity each frame.
//

import SpriteKit

final class Player: SKSpriteNode {

    // Tunables — chosen to be self-consistent with the scene gravity of
    // -2600 pts/s². Jump apex ≈ 900²/(2·2600) ≈ 156 pts (~5 tiles).
    private let moveSpeed: CGFloat = 340       // points / second
    private let jumpVelocity: CGFloat = 900     // initial upward velocity
    private let maxHealth = 5

    // State
    private(set) var health = 5
    private(set) var hasDoubleJump = false      // ability gate
    private var jumpsRemaining = 0
    private var onGround = false
    private var isInvulnerable = false
    private var facingRight = true

    /// -1 (left), 0 (idle), +1 (right). Set by the scene from touch input.
    var moveDirection: CGFloat = 0

    private var runFrames: [SKTexture] = []

    // MARK: - Setup

    static func make() -> Player {
        let frames = PixelArt.playerFrames()
        let texture = frames[0]
        // Size by target height so procedural (10×12) and bundled PNG (16×24)
        // art both render at the same in-world scale.
        let displaySize = PixelArt.displaySize(for: texture, targetHeight: 56)
        let player = Player(texture: texture, color: .clear, size: displaySize)
        player.runFrames = frames
        player.zPosition = 50
        player.name = "player"
        player.configurePhysics()
        player.addGlow()
        return player
    }

    private func configurePhysics() {
        // A capsule-ish body slightly narrower than the sprite for forgiving collisions.
        let bodySize = CGSize(width: size.width * 0.42, height: size.height * 0.9)
        let body = SKPhysicsBody(rectangleOf: bodySize, center: CGPoint(x: 0, y: 0))
        body.allowsRotation = false
        body.restitution = 0
        body.friction = 0.0
        body.linearDamping = 0.1
        body.mass = 0.6
        body.categoryBitMask = PhysicsCategory.player
        body.collisionBitMask = PhysicsCategory.ground
        // Grounding is handled by a ray-cast (see GameScene.updateGrounded), so
        // we don't need ground contact callbacks here — only gameplay triggers.
        body.contactTestBitMask = PhysicsCategory.enemy | PhysicsCategory.pickup |
                                  PhysicsCategory.door | PhysicsCategory.hazard
        physicsBody = body
    }

    private func addGlow() {
        let glow = SKSpriteNode(texture: texture)
        glow.size = size
        glow.color = Palette.player
        glow.colorBlendFactor = 1.0
        glow.alpha = 0.35
        glow.zPosition = -1
        glow.setScale(1.25)
        glow.blendMode = .add
        addChild(glow)
    }

    // MARK: - Per-frame update

    func update(deltaTime: TimeInterval) {
        guard let body = physicsBody else { return }

        // Horizontal velocity is set directly for snappy, arcade-style control.
        body.velocity.dx = moveDirection * moveSpeed

        if moveDirection > 0 { face(right: true) }
        else if moveDirection < 0 { face(right: false) }

        animate()
    }

    /// Called by the scene from contact detection.
    func setGrounded(_ grounded: Bool) {
        if grounded && !onGround {
            jumpsRemaining = hasDoubleJump ? 2 : 1
        }
        onGround = grounded
    }

    // MARK: - Actions

    func jump() {
        guard let body = physicsBody else { return }

        if onGround {
            jumpsRemaining = hasDoubleJump ? 2 : 1
        }
        guard jumpsRemaining > 0 else { return }

        jumpsRemaining -= 1
        onGround = false
        body.velocity.dy = jumpVelocity
        if jumpsRemaining == 0 && hasDoubleJump { spawnDoubleJumpPuff() }
    }

    func grantDoubleJump() {
        hasDoubleJump = true
        jumpsRemaining = max(jumpsRemaining, 1)
        flash(color: Palette.pickup)
    }

    @discardableResult
    func takeDamage(_ amount: Int, knockbackFrom point: CGPoint) -> Bool {
        guard !isInvulnerable, health > 0 else { return false }
        health = max(0, health - amount)
        applyKnockback(from: point)
        startInvulnerability()
        return true
    }

    func heal(_ amount: Int) {
        health = min(maxHealth, health + amount)
    }

    var isDead: Bool { health <= 0 }

    // MARK: - Feedback

    private func applyKnockback(from point: CGPoint) {
        guard let body = physicsBody else { return }
        let dir: CGFloat = position.x < point.x ? -1 : 1
        body.velocity = CGVector(dx: dir * 320, dy: 520)
    }

    private func startInvulnerability() {
        isInvulnerable = true
        let blink = SKAction.sequence([.fadeAlpha(to: 0.3, duration: 0.08),
                                       .fadeAlpha(to: 1.0, duration: 0.08)])
        run(.sequence([.repeat(blink, count: 6),
                       .run { [weak self] in self?.isInvulnerable = false }]),
            withKey: "invuln")
    }

    private func flash(color: SKColor) {
        let tint = SKAction.sequence([
            .colorize(with: color, colorBlendFactor: 0.8, duration: 0.06),
            .colorize(withColorBlendFactor: 0.0, duration: 0.2),
        ])
        run(tint)
    }

    private func spawnDoubleJumpPuff() {
        let puff = SKShapeNode(circleOfRadius: size.width * 0.4)
        puff.fillColor = Palette.player
        puff.strokeColor = .clear
        puff.alpha = 0.6
        puff.blendMode = .add
        puff.position = CGPoint(x: 0, y: -size.height * 0.4)
        puff.zPosition = -2
        addChild(puff)
        puff.run(.sequence([.group([.scale(to: 2.2, duration: 0.25),
                                    .fadeOut(withDuration: 0.25)]),
                            .removeFromParent()]))
    }

    // MARK: - Animation

    private func face(right: Bool) {
        guard right != facingRight else { return }
        facingRight = right
        xScale = right ? 1 : -1
    }

    private func animate() {
        let moving = abs(moveDirection) > 0.01 && onGround
        if moving {
            if action(forKey: "run") == nil, runFrames.count >= 3 {
                let cycle = SKAction.animate(with: [runFrames[1], runFrames[2]],
                                             timePerFrame: 0.12)
                run(.repeatForever(cycle), withKey: "run")
            }
        } else {
            removeAction(forKey: "run")
            if !runFrames.isEmpty { texture = runFrames[0] }
        }
    }
}
