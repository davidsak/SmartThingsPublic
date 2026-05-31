//
//  TouchControls.swift
//  Neon Citadel
//
//  On-screen D-pad + action buttons for touch play. The node is added to the
//  camera so it stays fixed on screen. The scene queries `hitTestButton` for
//  each active touch and reads the resulting intent each frame.
//

import SpriteKit

enum ControlButton: String {
    case left, right, jump, attack
}

final class TouchControls: SKNode {

    private(set) var buttons: [ControlButton: SKShapeNode] = [:]

    /// Lay the controls out for a given (landscape) view size. The camera's
    /// coordinate space has its origin at the screen centre.
    func layout(for size: CGSize) {
        removeAllChildren()
        buttons.removeAll()

        let halfW = size.width / 2
        let halfH = size.height / 2
        let r: CGFloat = 42
        let margin: CGFloat = 36

        // Movement pad, bottom-left.
        let padY = -halfH + margin + r
        addButton(.left,  at: CGPoint(x: -halfW + margin + r, y: padY), radius: r, glyph: "◀")
        addButton(.right, at: CGPoint(x: -halfW + margin + r * 3 + 16, y: padY), radius: r, glyph: "▶")

        // Action buttons, bottom-right.
        addButton(.jump,   at: CGPoint(x: halfW - margin - r, y: padY + r + 14), radius: r, glyph: "▲")
        addButton(.attack, at: CGPoint(x: halfW - margin - r * 2 - 18, y: padY - 6), radius: r * 0.9, glyph: "✦")
    }

    private func addButton(_ kind: ControlButton, at point: CGPoint, radius: CGFloat, glyph: String) {
        let node = SKShapeNode(circleOfRadius: radius)
        node.position = point
        node.fillColor = Palette.uiButton
        node.strokeColor = Palette.uiButtonStroke
        node.lineWidth = 2
        node.glowWidth = 1.5
        node.zPosition = 1000
        node.name = "ctrl_\(kind.rawValue)"

        let label = SKLabelNode(text: glyph)
        label.fontName = "Menlo-Bold"
        label.fontSize = radius * 0.9
        label.fontColor = Palette.uiText
        label.verticalAlignmentMode = .center
        label.horizontalAlignmentMode = .center
        node.addChild(label)

        addChild(node)
        buttons[kind] = node
    }

    /// Returns which control (if any) contains the given point in this node's space.
    func button(at point: CGPoint) -> ControlButton? {
        for (kind, node) in buttons {
            let dx = point.x - node.position.x
            let dy = point.y - node.position.y
            let r = node.frame.width / 2 + 8 // small touch slop
            if dx * dx + dy * dy <= r * r { return kind }
        }
        return nil
    }

    func setPressed(_ kind: ControlButton, _ pressed: Bool) {
        guard let node = buttons[kind] else { return }
        node.fillColor = pressed ? Palette.uiButtonStroke.withAlphaComponent(0.35)
                                 : Palette.uiButton
    }
}
