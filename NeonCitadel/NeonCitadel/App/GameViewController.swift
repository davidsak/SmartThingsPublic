//
//  GameViewController.swift
//  Neon Citadel
//
//  Hosts the SKView and presents the title scene. Configured for crisp,
//  pixel-accurate rendering and locked to landscape.
//

import UIKit
import SpriteKit

final class GameViewController: UIViewController {

    private var skView: SKView { view as! SKView }

    override func loadView() {
        // Use an SKView as the controller's root view.
        view = SKView(frame: UIScreen.main.bounds)
    }

    override func viewDidLoad() {
        super.viewDidLoad()

        skView.ignoresSiblingOrder = true
        skView.preferredFramesPerSecond = 60

        #if DEBUG
        skView.showsFPS = true
        skView.showsNodeCount = true
        skView.showsPhysics = false
        #endif
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        // Present the title scene once we have a real (laid-out) size.
        guard skView.scene == nil, skView.bounds.size != .zero else { return }
        let menu = MenuScene(size: skView.bounds.size)
        menu.scaleMode = .resizeFill
        skView.presentScene(menu)
    }

    override var supportedInterfaceOrientations: UIInterfaceOrientationMask {
        .landscape
    }

    override var prefersStatusBarHidden: Bool { true }

    override var prefersHomeIndicatorAutoHidden: Bool { true }
}
