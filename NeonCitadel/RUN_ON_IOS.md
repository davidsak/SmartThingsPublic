# Running Neon Citadel on iOS

Neon Citadel is a native **SpriteKit + Swift** app. Native iOS apps can only be
**compiled and signed with Xcode on a Mac** — there's no way around that part
(not from Linux, not from the iPhone itself). The good news: putting it on your
own iPhone/iPad is free and takes about 5 minutes once Xcode is installed.

There are three things people mean by "test on iPhone"; this doc covers all three:

1. **Play the real app on your iPhone** — build from your Mac, run on the device. ← main path
2. **Play instantly with no Mac** — the browser playtest (`WebPlaytest/play.html`).
3. **Run the automated tests** — where the logic/design suite runs (spoiler: Mac or this container, not the phone).

---

## 1. Build the real app onto your iPhone (Mac required)

### One-time setup
1. Install **Xcode 16+** from the Mac App Store (free). Launch it once so it
   finishes installing components.
2. Get this repo onto the Mac (clone it, or pull the
   `claude/80s-metroidvania-ios-game-ViV7X` branch).

### Open and run
3. Open the project:
   ```sh
   open NeonCitadel/NeonCitadel.xcodeproj
   ```
   (A shared **NeonCitadel** scheme is committed, so it's ready to build.)
4. Plug your iPhone into the Mac with a cable. On the phone, tap **Trust** if
   prompted. The first time, also enable **Developer Mode**:
   *Settings → Privacy & Security → Developer Mode → On*, then reboot.
5. In Xcode's toolbar, click the run-destination dropdown (top, next to the
   scheme) and pick **your iPhone** under the device list.
6. **Set a signing team** (free Apple ID works):
   - Select the **NeonCitadel** project in the left sidebar → **NeonCitadel**
     target → **Signing & Capabilities** tab.
   - Check **Automatically manage signing**.
   - **Team:** pick your Apple ID. If none is listed, click *Add an Account…*
     and sign in with your normal Apple ID — no paid account needed.
   - **Bundle Identifier:** change `com.example.NeonCitadel` to something unique
     to you, e.g. `com.yourname.NeonCitadel` (Apple requires it to be unique to
     your team).
7. Press **⌘R** (or the ▶ button). Xcode builds, installs, and launches it.

### First-launch trust step (free accounts only)
The first time you tap a self-signed app it won't open until you trust the
certificate:
- On the phone: **Settings → General → VPN & Device Management → [your Apple ID]
  → Trust**.
- Re-open the app from the Home Screen.

### Good to know with a free Apple ID
- The app is signed for **7 days**, then won't launch until you rebuild from
  Xcode (⌘R again — your save/progress logic, once added, persists).
- You can have a limited number of self-signed apps installed at once.
- A paid **Apple Developer Program** account ($99/yr) extends signing to a year
  and unlocks TestFlight/App Store. Not needed just to play it yourself.

### No cable? (wireless)
Once you've run it via cable at least once: in Xcode go to
**Window → Devices and Simulators**, select your iPhone, tick **Connect via
network**. After that you can build to it over Wi-Fi.

---

## 2. Play right now with no Mac — browser playtest

If you just want to *play* on the phone this second, open
**`WebPlaytest/play.html`** in Safari (AirDrop it to yourself, or host the repo
folder). It's a faithful port using the same constants and level as the real
game — touch controls, double-jump, the ability gate, the works. See
`WebPlaytest/README.md`.

> This is for testing feel/design, not the literal SpriteKit build. Use it to
> decide tuning; use the Xcode build (section 1) as ground truth.

Tip: in Safari, tap **Share → Add to Home Screen** and it launches full-screen
like a real app.

---

## 3. Running the automated tests

| Suite | What it checks | Where it runs |
|-------|----------------|---------------|
| `TestHarness/` (Python) | Game logic & level design (jump math, ability gate, winnability) | This Linux container, or your Mac: `cd NeonCitadel/TestHarness && python3 run_tests.py` |
| `WebPlaytest/` headless | The browser port is winnable end-to-end | Anywhere Node runs |
| **XCTest (not yet built)** | The *real* Swift code on a simulator/device | Mac only — ask me to scaffold it |

**Can the tests run on the iPhone itself?** Not the Python/Node suites — iOS has
no system Python/Node. The iOS-native way to "test on device" is an **XCUnit /
XCTest** target that Xcode runs *on* the iPhone (⌘U). I haven't built that yet;
if you want on-device tests, I'll factor the game rules into a small
`NeonCitadelCore` module and add an XCTest target so ⌘U runs the suite straight
on your phone. Say the word.

---

## Quick troubleshooting

| Symptom | Fix |
|--------|-----|
| "Signing for NeonCitadel requires a development team" | Set your Team under Signing & Capabilities (step 6). |
| "Failed to register bundle identifier" | The bundle id is taken — change it to something more unique (step 6). |
| App installs but won't open, "Untrusted Developer" | Trust the cert: Settings → General → VPN & Device Management (section 1). |
| "Could not launch … Developer Mode disabled" | Enable Developer Mode and reboot (step 4). |
| Device not shown in Xcode | Unlock the phone, tap Trust on the cable prompt, try a different cable/port. |
| Screen is rotated / controls off-screen | The game is **landscape-only** by design; turn the phone sideways. |
