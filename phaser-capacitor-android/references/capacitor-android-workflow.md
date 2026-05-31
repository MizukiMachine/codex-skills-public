# Capacitor Android Workflow for Phaser Games

Use this when setting up, running, debugging, or signing a Phaser game inside Capacitor Android.

## Toolchain Calibration

Capacitor Android builds with Gradle and the Android SDK. No macOS is required; it works on Windows, Linux, WSL2, and macOS.

Verify the project's Capacitor major version first:

```bash
npm ls @capacitor/core @capacitor/cli @capacitor/android
```

Then compare against the official Capacitor environment setup docs for that major version. Do not hardcode a JDK, Node, SDK, or target SDK version from memory. Prefer Android Studio's configured Gradle JDK unless the official docs or project policy require otherwise.

Useful checks:

```bash
node --version
npx cap doctor
adb devices
```

If `adb` is missing, add Android SDK `platform-tools` to `PATH` and ensure `ANDROID_HOME` or `ANDROID_SDK_ROOT` points at the SDK.

If the project is in WSL2 but the emulator is on Windows, do not assume Linux `adb` can see the Windows emulator. Read `references/windows-wsl-emulator-workflow.md` and choose one device host deliberately.

## One-Time Setup

From the project root:

```bash
npm install @capacitor/core
npm install -D @capacitor/cli
npm install @capacitor/android
```

Initialize Capacitor if needed:

```bash
npx cap init
```

Add Android:

```bash
npm run build
npx cap add android
npx cap sync android
```

## Day-to-Day Loop

```bash
npm run build
npx cap sync android
npx cap run android
```

Or open Android Studio:

```bash
npx cap open android
```

`cap sync` copies built web assets into `android/app/src/main/assets/public/` and updates native dependencies. `cap run` builds, installs, and launches on a connected device or emulator.

Prefer adding scripts that encode the sequence:

```json
{
  "scripts": {
    "android:sync": "npm run build && npx cap sync android",
    "android:run": "npm run build && npx cap sync android && npx cap run android",
    "android:open": "npm run build && npx cap sync android && npx cap open android"
  }
}
```

## Device and Emulator

List targets:

```bash
npx cap run android --list
```

Run a specific target:

```bash
npx cap run android --target <DEVICE_ID>
```

Physical device:
- Enable Developer options and USB debugging.
- Accept the RSA prompt.
- Confirm with `adb devices`.

Emulator:
- Create an AVD in Android Studio Device Manager.
- Use an Android platform supported by the project's Capacitor version.
- Prefer a recent Google APIs system image with hardware graphics enabled.

WSL2:
- If WSL2 emulator GUI controls are unreliable, keep building in WSL and run/install with Windows `adb.exe`.
- Convert WSL APK paths with `wslpath -w` before passing them to Windows tools.
- Run PowerShell commands from `/mnt/c` or another Windows filesystem directory to avoid UNC-current-directory failures.

## Config Notes

Typical Vite + Capacitor config:

```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.game',
  appName: 'My Phaser Game',
  webDir: 'dist',
  server: {
    androidScheme: 'https'
  }
};

export default config;
```

Notes:
- `appId` becomes the Gradle `applicationId`.
- `webDir` must contain the built `index.html`.
- Capacitor serves bundled assets from a local WebView origin.
- Do not rely on `file://` paths.
- Keep `server.androidScheme` at the project default unless routing requires a change.

## Live Reload

Live reload is only for development.

Use a reachable host:
- Physical device: your dev machine LAN IP.
- Android emulator: often `10.0.2.2` for the host machine.

Example:

```typescript
server: {
  url: 'http://10.0.2.2:5173',
  cleartext: true
}
```

Run Vite with host binding:

```bash
npm run dev -- --host 0.0.0.0
npx cap run android
```

Remove `server.url` before production builds unless the app intentionally uses a remote update system. Shipping `server.url` accidentally is a common release bug.

## WebView Debugging

For physical devices:
1. Enable USB debugging.
2. Connect the device.
3. Open desktop Chrome to `chrome://inspect`.
4. Inspect the WebView console, network failures, loader errors, audio policy errors, and WebGL errors.

For Android Studio:
- Use Logcat for native Gradle/plugin/lifecycle issues.
- Use Chrome WebView inspect for JavaScript, asset path, WebGL, and Phaser loader issues.

Add runtime breadcrumbs for Phaser failures:

```ts
this.load.on('loaderror', (file: Phaser.Loader.File) => {
  console.error('Phaser load failed', file.key, file.src);
});
```

## Signing a Release

Debug builds auto-sign. Release builds need a project-owned keystore.

Generate one:

```bash
keytool -genkey -v -keystore my-release.jks -keyalg RSA \
  -keysize 2048 -validity 10000 -alias my-game
```

Store secrets outside git. A common pattern is `android/keystore.properties` with:

```properties
storeFile=../my-release.jks
storePassword=****
keyAlias=my-game
keyPassword=****
```

Wire it in `android/app/build.gradle` using the project's existing Gradle style, then build with:

```bash
cd android
./gradlew bundleRelease
./gradlew assembleRelease
```

Use Android Studio, official Android docs, or official Capacitor docs as source of truth for permissions, target SDK, Play Store requirements, and signing policy.
