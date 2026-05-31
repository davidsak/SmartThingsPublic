//
//  LevelBuilder.swift
//  Neon Citadel
//
//  Parses Level.map and populates a scene with tiles and entities. Adjacent
//  solid tiles share a single tiled-texture sprite for visuals, but each gets
//  its own physics body (simple and robust for a vertical slice).
//

import SpriteKit

struct LevelContents {
    var playerSpawn: CGPoint = .zero
    var enemies: [Enemy] = []
    var pickup: AbilityPickup?
    var door: AbilityDoor?
    var goal: SKNode?
}

enum LevelBuilder {

    @discardableResult
    static func build(into worldNode: SKNode) -> LevelContents {
        var contents = LevelContents()
        let tileTexture = PixelArt.tileTexture()
        let backTexture = PixelArt.backTileTexture()
        let size = Level.tileSize

        for (row, line) in Level.map.enumerated() {
            for (col, ch) in line.enumerated() {
                let pos = Level.position(col: col, row: row)
                switch ch {
                case "X":
                    worldNode.addChild(makeTile(texture: tileTexture, size: size, at: pos))
                case "b":
                    worldNode.addChild(makeBackTile(texture: backTexture, size: size, at: pos))
                case "P":
                    contents.playerSpawn = pos
                case "E":
                    let enemy = Enemy.make(patrolWidth: size * 5)
                    enemy.position = pos
                    worldNode.addChild(enemy)
                    enemy.anchorPatrol()
                    contents.enemies.append(enemy)
                case "C":
                    let pickup = AbilityPickup.make()
                    pickup.position = pos
                    worldNode.addChild(pickup)
                    contents.pickup = pickup
                case "D":
                    let door = AbilityDoor.make(height: size * 3)
                    // Sit the door so its base rests on the tile row below it.
                    door.position = CGPoint(x: pos.x, y: pos.y + size)
                    worldNode.addChild(door)
                    contents.door = door
                case "G":
                    let goal = makeGoal(size: size, at: pos)
                    worldNode.addChild(goal)
                    contents.goal = goal
                default:
                    break
                }
            }
        }
        return contents
    }

    private static func makeTile(texture: SKTexture, size: CGFloat, at pos: CGPoint) -> SKSpriteNode {
        let tile = SKSpriteNode(texture: texture, size: CGSize(width: size, height: size))
        tile.position = pos
        tile.zPosition = 10
        let body = SKPhysicsBody(rectangleOf: tile.size)
        body.isDynamic = false
        body.friction = 0.2
        body.restitution = 0
        body.categoryBitMask = PhysicsCategory.ground
        tile.physicsBody = body
        return tile
    }

    private static func makeBackTile(texture: SKTexture, size: CGFloat, at pos: CGPoint) -> SKSpriteNode {
        let tile = SKSpriteNode(texture: texture, size: CGSize(width: size, height: size))
        tile.position = pos
        tile.zPosition = 2
        tile.alpha = 0.65
        return tile
    }

    private static func makeGoal(size: CGFloat, at pos: CGPoint) -> SKNode {
        let container = SKNode()
        container.position = pos
        container.name = "goal"
        container.zPosition = 35

        // A glowing portal ring.
        let ring = SKShapeNode(circleOfRadius: size * 0.55)
        ring.strokeColor = Palette.grid
        ring.lineWidth = 4
        ring.glowWidth = 6
        ring.fillColor = Palette.grid.withAlphaComponent(0.15)
        container.addChild(ring)

        let inner = SKShapeNode(circleOfRadius: size * 0.3)
        inner.strokeColor = Palette.sun
        inner.lineWidth = 3
        inner.glowWidth = 4
        inner.fillColor = .clear
        container.addChild(inner)

        let body = SKPhysicsBody(circleOfRadius: size * 0.5)
        body.isDynamic = false
        body.categoryBitMask = PhysicsCategory.door   // reuse: contact-only trigger
        body.collisionBitMask = PhysicsCategory.none
        body.contactTestBitMask = PhysicsCategory.player
        container.physicsBody = body

        container.run(.repeatForever(.rotate(byAngle: .pi * 2, duration: 6)))
        inner.run(.repeatForever(.rotate(byAngle: -.pi * 2, duration: 4)))
        return container
    }
}
