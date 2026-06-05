# Capacitor Android Workflow for Three.js Apps

Use this when setting up, running, debugging, or signing a Three.js app inside Capacitor Android.

## Toolchain Calibration

Capacitor Android builds with Gradle and the Android SDK. No macOS is required; it works on Windows, Linux, WSL2, and macOS.

Verify the project's Capacitor major version first:

```bash
npm ls @capacitor/core @capacitor/cli @capacitor/android
```

Then compare against the official Capacitor environment setup docs for that major version. For current Capacitor 8-era projects, the important defaults are:
- Node 22+
- Android Studio with Android SDK
- Android SDK platform API 24+
- Android Studio's bundled Gradle JDK for most local workflows

Do not hardcode a JDK version from memory. If `JAVA_HOME` is needed, set it to the Gradle JDK path shown in Android Studio: Settings/Preferences > Build, Execution, Deployment > Build Tools > Gradle > Gradle JDK. As a rule of thumb the JDK must match the Capacitor major version (e.g. Capacitor 8 → JDK 17+), but always defer to the docs.

Useful checks:

```bash
node --version
npx cap doctor
adb devices
```

If `adb` is missing, add Android SDK `platform-tools` to PATH and ensure `ANDROID_HOME` or `ANDROID_SDK_ROOT` points at the SDK.

If the project is in WSL2 but the emulator is on Windows, do not assume Linux `adb` can see the Windows emulator. Read `references/windows-wsl-emulator-workflow.md` and choose one device host deliberately.

## One-Time Setup

From the project root:

```bash
npm install @capacitor/core@latest
npm install -D @capacitor/cli@latest
npm install @capacitor/android@latest
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

`cap sync` copies built web assets into `android/app/src/main/assets/public/` and updates native dependencies. `cap run` builds, installs, and launches on a connected device or emulator via Gradle.

Prefer adding scripts that encode the sequence so build/sync can't be skipped:

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
- Use API 24+.
- Prefer a recent Google APIs system image with hardware GL enabled.

WSL2:
- If WSL2 emulator GUI controls are unreliable, keep building in WSL and run/install with Windows `adb.exe`.
- Convert WSL APK paths with `wslpath -w` before passing them to Windows tools.
- Run PowerShell commands from `/mnt/c` or another Windows filesystem directory to avoid UNC-current-directory failures.
- Full procedure: `references/windows-wsl-emulator-workflow.md`.

## Config Notes

Typical Vite config:

```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.app',     // becomes the Gradle applicationId
  appName: 'My Three App',
  webDir: 'dist',               // must contain the built index.html
  server: {
    androidScheme: 'https',     // default; assets served from https://localhost
  },
};

export default config;
```

Notes:
- `appId` becomes the Gradle `applicationId`.
- `webDir` must contain the built `index.html`.
- `server.androidScheme` defaults to `https`; keep it unless a route strategy forces a change. Absolute `/assets/...` URLs resolve correctly under that origin.
- `android.allowMixedContent: true` only if you must load `http://` assets.
- Do not rely on `file://` paths. Bundled assets are served from a local WebView origin.

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

## Validation

```bash
npx cap doctor
```

Look for:
- matching `@capacitor/*` versions
- Android status healthy
- sync writing the native project correctly

## WebView Debugging

For physical devices:
1. Enable USB debugging.
2. Connect the device.
3. Open desktop Chrome to `chrome://inspect`.
4. Inspect the WebView console, network failures, and WebGL errors.

For Android Studio:
- Use Logcat for native Gradle/plugin/lifecycle issues.
- Use Chrome WebView inspect for JS, asset path, and WebGL issues.

## Signing a Release

Debug builds auto-sign with a debug key. Release builds need a project-owned keystore.

Generate one:

```bash
keytool -genkey -v -keystore my-release.jks -keyalg RSA \
  -keysize 2048 -validity 10000 -alias my-app
```

Store secrets outside git. A common pattern is `android/keystore.properties` (gitignore it) with:

```properties
storeFile=../my-release.jks
storePassword=****
keyAlias=my-app
keyPassword=****
```

Wire it in `android/app/build.gradle`:

```gradle
def keystoreProps = new Properties()
def keystoreFile = rootProject.file("keystore.properties")
if (keystoreFile.exists()) {
    keystoreProps.load(new FileInputStream(keystoreFile))
}

android {
    signingConfigs {
        release {
            storeFile file(keystoreProps['storeFile'])
            storePassword keystoreProps['storePassword']
            keyAlias keystoreProps['keyAlias']
            keyPassword keystoreProps['keyPassword']
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

Build:

```bash
cd android
./gradlew bundleRelease    # -> app-release.aab (Play Store)
./gradlew assembleRelease  # -> app-release.apk (sideload)
```

Use Android Studio or official Android/Capacitor docs as source of truth for permissions (`android/app/src/main/AndroidManifest.xml`), target SDK, Play Store requirements, and signing policy.
