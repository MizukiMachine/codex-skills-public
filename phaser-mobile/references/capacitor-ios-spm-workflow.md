# Capacitor iOS SPM Workflow for Phaser Games

Use this when setting up, running, debugging, migrating, or signing a Phaser game inside Capacitor iOS.

## Toolchain Calibration

Capacitor iOS requires Apple's iOS toolchain for local builds.

Verify the project's Capacitor major version first:

```bash
npm ls @capacitor/core @capacitor/cli @capacitor/ios
```

Then compare against the official Capacitor environment setup docs for that major version. Do not hardcode Node, Xcode, Command Line Tools, deployment target, or package-manager requirements from memory.

Useful checks:

```bash
node --version
xcode-select -p
npx cap doctor
```

Install Command Line Tools if missing:

```bash
xcode-select --install
```

## Why SPM

Swift Package Manager is the preferred iOS dependency manager in modern Capacitor. Use SPM unless an existing project or plugin explicitly requires CocoaPods.

Do not edit Capacitor-generated SPM package internals such as `CapApp-SPM` manually. The Capacitor CLI can rewrite them during sync.

## One-Time Setup

From the project root:

```bash
npm install @capacitor/core
npm install -D @capacitor/cli
npm install @capacitor/ios
```

Initialize Capacitor if needed:

```bash
npx cap init
```

Add iOS with SPM:

```bash
npm run build
npx cap add ios --packagemanager SPM
npx cap sync ios
```

The CLI accepts `--packagemanager SPM` for SPM and `--packagemanager Cocoapods` when CocoaPods is explicitly needed.

## Day-to-Day Loop

```bash
npm run build
npx cap sync ios
npx cap run ios
```

Or open Xcode:

```bash
npx cap open ios
```

Prefer adding scripts that encode the sequence:

```json
{
  "scripts": {
    "ios:sync": "npm run build && npx cap sync ios",
    "ios:run": "npm run build && npx cap sync ios && npx cap run ios",
    "ios:open": "npm run build && npx cap sync ios && npx cap open ios"
  }
}
```

## Simulator and Device

List targets:

```bash
npx cap run ios --list
```

Run a specific target:

```bash
npx cap run ios --target <TARGET_ID>
```

Simulator:
- Use Xcode's Devices and Simulators UI when target availability is unclear.
- If simulator state is stale, erase content/settings before debugging app logic.
- Capture simulator screenshots when checking canvas, safe areas, orientation, or pixel-art rendering.

Physical device:
- Requires Apple Developer signing.
- Trust the developer certificate on device if prompted.
- Wireless devices must be paired and visible to Xcode/Finder before `npx cap run ios --list` can see them.
- Real devices are the source of truth for touch latency, audio behavior, safe areas, memory pressure, and performance.

## Migrating from CocoaPods to SPM

Two practical options:

1. Recreate the iOS platform with the SPM template after backing up any manual native changes:

```bash
npm run build
rm -rf ios
npx cap add ios --packagemanager SPM
npx cap sync ios
```

Only remove `ios/` when you have confirmed native changes are disposable or backed up.

2. Use the migration helper:

```bash
npx cap spm-migration-assistant
```

Then run `npx cap open ios` and verify the local `CapApp-SPM` package is added in Xcode Package Dependencies. The migration tool may warn about plugins that cannot be represented as SPM packages.

## Config Notes

Typical Vite + Capacitor config:

```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.game',
  appName: 'My Phaser Game',
  webDir: 'dist'
};

export default config;
```

Notes:
- `appId` becomes the iOS bundle identifier unless changed in Xcode.
- `webDir` must contain the built `index.html`.
- Do not rely on `file://` paths. Bundled assets are served inside WKWebView by Capacitor.
- Update iOS orientation, capabilities, and permission strings in the native project when plugins or product behavior require it.

## Live Reload

Live reload is only for development.

Use a reachable LAN host:

```typescript
server: {
  url: 'http://192.168.1.50:5173'
}
```

Run Vite with host binding:

```bash
npm run dev -- --host 0.0.0.0
npx cap run ios
```

Remove `server.url` before production builds unless the app intentionally uses a remote update system. Shipping `server.url` accidentally is a common release bug.

## WKWebView Debugging

For simulator/device WebView issues:
- Enable Safari Develop menu on macOS.
- Use Safari > Develop > Simulator or device > app WebView.
- Inspect console, network failures, Phaser loader errors, asset paths, audio policy errors, and WebGL errors.

Use Xcode logs for native build, signing, package resolution, lifecycle, and plugin issues.

Add runtime breadcrumbs for Phaser failures:

```ts
this.load.on('loaderror', (file: Phaser.Loader.File) => {
  console.error('Phaser load failed', file.key, file.src);
});
```

## Signing and Release

For release builds:
- Set the bundle identifier.
- Select a team in Xcode Signing & Capabilities.
- Add required capabilities.
- Fill `Info.plist` permission usage strings when plugins require them.
- Archive from Xcode or CI.

For App Store submission, follow Apple's current requirements for privacy manifest, signing, provisioning, archive/export, and TestFlight/App Store Connect.

Use official iOS configuration, Capacitor, and App Store deployment docs as source of truth for permissions and signing policy.
