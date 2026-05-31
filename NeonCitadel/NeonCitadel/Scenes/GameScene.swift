//
//  GameScene.swift
//  Neon Citadel
//
//  The playable vertical slice: builds the level, drives the player and enemies,
//  resolves contacts (pickup → ability → gated door → goal), runs the camera,
//  and handles touch input from the on-screen controls.
//

import SpriteKit

final class GameScene: SKScene, SKPhysicsContactDelegate {

    // World gravity tuned to match Player's jump constants.
    private let gravity = CGVector(dx: 0, dy: -2600)

    private let worldNode = SKNode()
    private let cameraNode = SKCameraNode()

    private var player: Player!
    private var hud: HUD!
    private var controls = TouchControls()
    private var contents = LevelContents()

    private var lastUpdateTime: TimeInterval = 0
    private var leftHeld = false
    private var rightHeld = false
    private var touchButtons: [ObjectIdentifier: ControlButton] = [:]
    private var isGameOver = false
    private var shakeOffset: CGPoint = .zero

    private let maxHealth = 5

    // MARK: - Setup

    override func didMove(to view: SKView) {
        backgroundColor = Palette.background
        scaleMode = .resizeFill

        physicsWorld.gravity = gravity
        physicsWorld.contactDelegate = self

        addChild(worldNode)

        // Build the level into the world node.
        contents = LevelBuilder.build(into: worldNode)

        // Player.
        player = Player.make()
        player.position = contents.playerSpawn
        worldNode.addChild(player)

        // Camera + screen-fixed UI. The backdrop is (re)created in layoutUI().
        addChild(cameraNode)
        camera = cameraNode

        hud = HUD(maxHealth: maxHealth)
        cameraNode.addChild(hud)
        cameraNode.addChild(controls)

        layoutUI()
        hud.setHealth(player.health)

        updateCamera()
    }

    override func didChangeSize(_ oldSize: CGSize) {
        super.didChangeSize(oldSize)
        guard cameraNode.parent != nil else { return }
        layoutUI()
    }

    private func layoutUI() {
        controls.layout(for: size)
        hud.layout(for: size)
        hud.setHealth(player?.health ?? maxHealth)
        if player?.hasDoubleJump == true { hud.setAbilityUnlocked() }
        // Re-fit the backdrop to the (possibly new) size.
        cameraNode.childNode(withName: "backdrop")?.removeFromParent()
        let bg = Background.make(for: size)
        bg.name = "backdrop"
        cameraNode.addChild(bg)
    }

    // MARK: - Game loop

    override func update(_ currentTime: TimeInterval) {
        let dt = lastUpdateTime == 0 ? 0 : min(currentTime - lastUpdateTime, 1.0 / 30.0)
        lastUpdateTime = currentTime
        guard !isGameOver else { return }

        updateGrounded()
        player.update(deltaTime: dt)
        contents.enemies.forEach { $0.update(deltaTime: dt) }

        // Fell out of the world.
        if player.position.y < -50 {
            respawnAfterFall()
        }
    }

    override func didFinishUpdate() {
        guard !isGameOver else { return }
        updateCamera()
    }

    /// Downward ray-cast from the player's feet for reliable ground detection
    /// (avoids the wall-jump bug you get from naive contact counting).
    private func updateGrounded() {
        guard let body = player.physicsBody else { return }
        let feet = CGPoint(x: player.position.x, y: player.position.y - player.size.height * 0.5)
        let end = CGPoint(x: feet.x, y: feet.y - 8)
        var grounded = false
        physicsWorld.enumerateBodies(alongRayStart: feet, end: end) { b, _, _, stop in
            if b.categoryBitMask & PhysicsCategory.ground != 0 {
                grounded = true
                stop.pointee = true
            }
        }
        player.setGrounded(grounded && body.velocity.dy <= 1)
    }

    private func updateCamera() {
        let target = clampedCamera(to: player.position)
        cameraNode.position = CGPoint(x: target.x + shakeOffset.x,
                                      y: target.y + shakeOffset.y)
    }

    private func clampedCamera(to point: CGPoint) -> CGPoint {
        let halfW = size.width / 2
        let halfH = size.height / 2
        let w = Level.worldWidth
        let h = Level.worldHeight

        let x: CGFloat
        if w <= size.width { x = w / 2 }
        else { x = min(max(point.x, halfW), w - halfW) }

        let y: CGFloat
        if h <= size.height { y = h / 2 }
        else { y = min(max(point.y, halfH), h - halfH) }

        return CGPoint(x: x, y: y)
    }

    // MARK: - Touch input

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        for touch in touches { register(touch) }
        refreshMovement()
    }

    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        for touch in touches {
            let id = ObjectIdentifier(touch)
            let previous = touchButtons[id]
            let current = controls.button(at: touch.location(in: cameraNode))
            if current != previous {
                if let p = previous { release(p) }
                if let c = current, c == .left || c == .right {
                    touchButtons[id] = c
                    controls.setPressed(c, true)
                } else {
                    touchButtons[id] = nil
                }
            }
        }
        refreshMovement()
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        endTouches(touches)
    }

    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        endTouches(touches)
    }

    private func register(_ touch: UITouch) {
        let loc = touch.location(in: cameraNode)
        guard let kind = controls.button(at: loc) else { return }
        controls.setPressed(kind, true)
        switch kind {
        case .left, .right:
            touchButtons[ObjectIdentifier(touch)] = kind
        case .jump:
            player.jump()
            controls.run(.wait(forDuration: 0.08)) { [weak self] in self?.controls.setPressed(.jump, false) }
        case .attack:
            performAttack()
            controls.run(.wait(forDuration: 0.12)) { [weak self] in self?.controls.setPressed(.attack, false) }
        }
    }

    private func endTouches(_ touches: Set<UITouch>) {
        for touch in touches {
            let id = ObjectIdentifier(touch)
            if let kind = touchButtons[id] { release(kind) }
            touchButtons[id] = nil
        }
        refreshMovement()
    }

    private func release(_ kind: ControlButton) {
        controls.setPressed(kind, false)
    }

    private func refreshMovement() {
        let held = Set(touchButtons.values)
        leftHeld = held.contains(.left)
        rightHeld = held.contains(.right)
        player.moveDirection = (rightHeld ? 1 : 0) - (leftHeld ? 1 : 0)
    }

    // MARK: - Attack

    private func performAttack() {
        guard !isGameOver else { return }
        let facing: CGFloat = player.xScale >= 0 ? 1 : -1
        let reach = player.size.width * 0.9

        // Visual slash.
        let slash = SKShapeNode(circleOfRadius: reach * 0.6)
        slash.strokeColor = Palette.player
        slash.lineWidth = 3
        slash.glowWidth = 4
        slash.fillColor = .clear
        slash.position = CGPoint(x: player.position.x + facing * reach * 0.6,
                                 y: player.position.y)
        slash.zPosition = 60
        slash.alpha = 0.9
        worldNode.addChild(slash)
        slash.run(.sequence([.group([.scale(to: 1.4, duration: 0.12),
                                     .fadeOut(withDuration: 0.12)]),
                             .removeFromParent()]))

        // Hit sensor.
        let sensor = SKNode()
        sensor.position = slash.position
        let body = SKPhysicsBody(rectangleOf: CGSize(width: reach, height: player.size.height * 0.8))
        body.isDynamic = true
        body.affectedByGravity = false
        body.categoryBitMask = PhysicsCategory.attack
        body.collisionBitMask = PhysicsCategory.none
        body.contactTestBitMask = PhysicsCategory.enemy
        sensor.physicsBody = body
        worldNode.addChild(sensor)
        sensor.run(.sequence([.wait(forDuration: 0.08), .removeFromParent()]))
    }

    // MARK: - Contacts

    func didBegin(_ contact: SKPhysicsContact) {
        let a = contact.bodyA
        let b = contact.bodyB
        let nodeA = a.node
        let nodeB = b.node

        // Attack hits enemy.
        if let enemy = (nodeA as? Enemy) ?? (nodeB as? Enemy),
           (a.categoryBitMask | b.categoryBitMask) & PhysicsCategory.attack != 0 {
            killEnemy(enemy)
            return
        }

        // Anything else must involve the player.
        guard let other = otherNode(in: contact, besides: player) else { return }

        switch other {
        case let enemy as Enemy:
            handlePlayerEnemy(enemy)
        case let pickup as AbilityPickup:
            handlePickup(pickup)
        case let door as AbilityDoor:
            handleDoor(door)
        default:
            if other.name == "goal" { handleGoal() }
        }
    }

    private func otherNode(in contact: SKPhysicsContact, besides node: SKNode) -> SKNode? {
        if contact.bodyA.node === node { return contact.bodyB.node }
        if contact.bodyB.node === node { return contact.bodyA.node }
        return nil
    }

    private func handlePlayerEnemy(_ enemy: Enemy) {
        guard !isGameOver else { return }
        // Stomp: player descending and clearly above the enemy.
        let stomping = (player.physicsBody?.velocity.dy ?? 0) < 0 &&
                       player.position.y > enemy.position.y + enemy.size.height * 0.2
        if stomping {
            killEnemy(enemy)
            player.physicsBody?.velocity.dy = 760   // bounce
        } else if player.takeDamage(enemy.touchDamage, knockbackFrom: enemy.position) {
            hud.setHealth(player.health)
            cameraShake()
            if player.isDead { gameOver(won: false) }
        }
    }

    private func killEnemy(_ enemy: Enemy) {
        guard enemy.parent != nil else { return }
        enemy.die()
        contents.enemies.removeAll { $0 === enemy }
    }

    private func handlePickup(_ pickup: AbilityPickup) {
        guard contents.pickup === pickup, pickup.parent != nil else { return }
        contents.pickup = nil
        pickup.collect { }
        player.grantDoubleJump()
        hud.setAbilityUnlocked()
        hud.showBanner("DOUBLE JUMP ACQUIRED", color: Palette.pickup)
    }

    private func handleDoor(_ door: AbilityDoor) {
        guard !door.isOpen else { return }
        if player.hasDoubleJump {
            door.open()
            hud.showBanner("GATE UNLOCKED", color: Palette.door)
        } else {
            hud.showBanner("LOCKED — FIND THE CORE", color: Palette.doorLock)
        }
    }

    private func handleGoal() {
        guard !isGameOver else { return }
        gameOver(won: true)
    }

    // MARK: - Outcomes

    private func respawnAfterFall() {
        if player.takeDamage(1, knockbackFrom: player.position) {
            hud.setHealth(player.health)
        }
        player.physicsBody?.velocity = .zero
        player.position = contents.playerSpawn
        if player.isDead { gameOver(won: false) }
    }

    private func gameOver(won: Bool) {
        guard !isGameOver else { return }
        isGameOver = true
        player.moveDirection = 0
        player.physicsBody?.velocity = .zero

        hud.showBanner(won ? "LEVEL CLEAR" : "GAME OVER",
                       color: won ? Palette.grid : Palette.enemy)

        run(.sequence([.wait(forDuration: 2.2), .run { [weak self] in
            guard let self else { return }
            let menu = MenuScene(size: self.size)
            menu.scaleMode = .resizeFill
            self.view?.presentScene(menu, transition: .crossFade(withDuration: 0.6))
        }]))
    }

    private func cameraShake() {
        // Drive a decaying offset that updateCamera() applies on top of the
        // follow target (the follow code overwrites position every frame, so a
        // plain moveBy action on the camera would be cancelled out).
        let duration = 0.25
        let magnitude: CGFloat = 11
        let decay = SKAction.customAction(withDuration: duration) { [weak self] _, elapsed in
            let k = (1 - elapsed / CGFloat(duration)) * magnitude
            self?.shakeOffset = CGPoint(x: .random(in: -k...k), y: .random(in: -k...k))
        }
        run(.sequence([decay, .run { [weak self] in self?.shakeOffset = .zero }]),
            withKey: "cameraShake")
    }
}
