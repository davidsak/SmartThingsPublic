//
//  MenuScene.swift
//  Neon Citadel
//
//  Title screen. Tap anywhere to drop into the game.
//

import SpriteKit

final class MenuScene: SKScene {

    override func didMove(to view: SKView) {
        backgroundColor = Palette.background
        scaleMode = .resizeFill

        let bg = Background.make(for: size)
        bg.position = CGPoint(x: size.width / 2, y: size.height / 2)
        addChild(bg)

        let title = SKLabelNode(text: "ASHEN VIGIL")
        title.fontName = "AvenirNextCondensed-Heavy"
        title.fontSize = 64
        title.fontColor = Palette.grid
        title.position = CGPoint(x: size.width / 2, y: size.height * 0.62)
        title.zPosition = 10
        addChild(title)

        let shadow = title.copy() as! SKLabelNode
        shadow.fontColor = Palette.sun
        shadow.position = CGPoint(x: title.position.x + 3, y: title.position.y - 3)
        shadow.zPosition = 9
        shadow.alpha = 0.8
        addChild(shadow)

        let subtitle = SKLabelNode(text: "A GOTHIC METROIDVANIA")
        subtitle.fontName = "Menlo-Bold"
        subtitle.fontSize = 18
        subtitle.fontColor = Palette.sun
        subtitle.position = CGPoint(x: size.width / 2, y: size.height * 0.52)
        subtitle.zPosition = 10
        addChild(subtitle)

        let prompt = SKLabelNode(text: "TAP TO START")
        prompt.fontName = "Menlo-Bold"
        prompt.fontSize = 24
        prompt.fontColor = Palette.uiText
        prompt.position = CGPoint(x: size.width / 2, y: size.height * 0.3)
        prompt.zPosition = 10
        prompt.run(.repeatForever(.sequence([.fadeAlpha(to: 0.25, duration: 0.7),
                                             .fadeAlpha(to: 1.0, duration: 0.7)])))
        addChild(prompt)

        let hint = SKLabelNode(text: "◀ ▶ move    ▲ jump    ✦ attack")
        hint.fontName = "Menlo"
        hint.fontSize = 14
        hint.fontColor = Palette.uiText.withAlphaComponent(0.7)
        hint.position = CGPoint(x: size.width / 2, y: size.height * 0.16)
        hint.zPosition = 10
        addChild(hint)
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        let scene = GameScene(size: size)
        scene.scaleMode = .resizeFill
        view?.presentScene(scene, transition: .crossFade(withDuration: 0.6))
    }
}
