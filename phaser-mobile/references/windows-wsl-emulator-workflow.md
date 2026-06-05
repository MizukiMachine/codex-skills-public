# WSL2 Project with Windows Android Emulator

Use this when the Phaser project lives in WSL2/Linux but Android Studio, `adb.exe`, or the emulator should run on Windows. This is common when a WSL2 emulator boots but its side toolbar, rotation, home, back, or power controls are unreliable, or when the user's actual Android toolchain is Windows native.

Default posture: Windows is the device host. Build and sync the web/native project in WSL, then use Windows native Android Studio/Emulator/`adb.exe` deliberately. Do not let `npx cap run android` or `npx cap open android` from WSL choose the Android Studio, SDK, or ADB host implicitly.

## Decision Rule

Prefer the WSL-built APK plus Windows `adb.exe` when:
- the APK already builds in WSL
- the goal is to run or smoke-test the game
- the changes are mostly TypeScript, Phaser scenes, CSS, assets, tilemaps, Capacitor config, or Android manifest values already synced
- Windows Android Studio/Gradle setup is unnecessary for the current check

Prefer Windows native Android Studio when:
- the user needs Gradle sync UI, Logcat, profilers, Device Manager, signing UI, or manifest/resource editors
- native Android code or Gradle files are the main work
- the project will be maintained primarily from Windows

Avoid opening a WSL UNC path in Windows tools as the first move unless the user explicitly wants that workflow. UNC paths can be slower, and some command-line tools start in `\\wsl.localhost\...`, which `cmd.exe` does not support as a current directory. For long native Android work, prefer a Windows filesystem clone. For short inspection, explicitly launch Windows `studio64.exe` with `wslpath -w "$PWD/android"`.

Do not recommend plain `npx cap run android` or `npx cap open android` as the WSL2 default. Those commands may open WSL-side Android Studio or talk to Linux `adb`, which is the wrong host when Windows owns the emulator.

## Discovery Checklist

From WSL project root:

```bash
sed -n '1,220p' package.json
sed -n '1,220p' capacitor.config.*
npm ls @capacitor/core @capacitor/cli @capacitor/android
npx cap doctor
test -f android/app/build/outputs/apk/debug/app-debug.apk && stat android/app/build/outputs/apk/debug/app-debug.apk
```

From WSL, query Windows from a Windows filesystem working directory such as `/mnt/c` to avoid UNC-current-directory problems:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$ErrorActionPreference="SilentlyContinue"; foreach ($name in "adb.exe","emulator.exe","studio64.exe") { $cmd = Get-Command $name; if ($cmd) { "$name=$($cmd.Source)" } else { "$name=NOT_IN_PATH" } }'

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$paths = @("$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe", "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe", "$env:ProgramFiles\Android\Android Studio\bin\studio64.exe"); foreach ($p in $paths) { if (Test-Path $p) { "FOUND=$p" } else { "MISSING=$p" } }'
```

If Windows SDK tools are not on `PATH`, use the default full paths. Do not assume `PATH` is configured.

## Recommended WSL-to-Windows Smoke Test

Use this shape for game/frontend changes:

```bash
npm run build
npx cap sync android
cd android
./gradlew assembleDebug
cd ..

ADB_WIN=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$env:LOCALAPPDATA + "\Android\Sdk\platform-tools\adb.exe"' | tr -d '\r')
ADB=$(wslpath -u "$ADB_WIN")
APK_WIN=$(wslpath -w "$PWD/android/app/build/outputs/apk/debug/app-debug.apk")

"$ADB" devices -l
"$ADB" -s emulator-5554 install -r "$APK_WIN"
"$ADB" -s emulator-5554 shell am start -n com.example.game/.MainActivity
```

Prefer adding project scripts that encode this workflow, for example:

```json
{
  "scripts": {
    "android:apk": "npm run build && npx cap sync android && cd android && ./gradlew assembleDebug",
    "android:install:windows": "npm run android:apk && node scripts/install-android-windows-adb.mjs",
    "android:studio:windows": "node scripts/open-android-studio-windows.mjs"
  }
}
```

The exact script names should match the project. The important contract is:
- WSL builds/syncs/APK-produces.
- Windows `adb.exe` installs and launches.
- Windows `studio64.exe` is used explicitly when Android Studio is needed.

## Windows ADB From WSL

Use Windows `adb.exe` when Windows owns the emulator:

```bash
ADB_WIN=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$env:LOCALAPPDATA + "\Android\Sdk\platform-tools\adb.exe"' | tr -d '\r')
ADB=$(wslpath -u "$ADB_WIN")
"$ADB" devices -l
```

If the APK path is in WSL, convert it before passing it to Windows `adb.exe`:

```bash
APK_WIN=$(wslpath -w "$PWD/android/app/build/outputs/apk/debug/app-debug.apk")
"$ADB" -s emulator-5554 install -r "$APK_WIN"
"$ADB" -s emulator-5554 shell am start -n com.example.game/.MainActivity
```

Find the real package and activity when uncertain:

```bash
"$ADB" -s emulator-5554 shell cmd package resolve-activity --brief com.example.game
"$ADB" -s emulator-5554 shell pm list packages | rg 'example|game'
```

Use one ADB host consistently. If device state looks stale, restart the Windows ADB server:

```bash
"$ADB" kill-server
"$ADB" start-server
"$ADB" devices -l
```

## Windows Native Android Studio From WSL

Use Windows Android Studio explicitly when native Android UI tools are needed:

```bash
STUDIO_WIN=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$p="$env:ProgramFiles\Android\Android Studio\bin\studio64.exe"; if (Test-Path $p) { $p } else { (Get-Command studio64.exe).Source }' | tr -d '\r')
ANDROID_PROJECT_WIN=$(wslpath -w "$PWD/android")

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "Start-Process -FilePath '$STUDIO_WIN' -ArgumentList @('$ANDROID_PROJECT_WIN')"
```

Run the PowerShell process from a Windows filesystem working directory such as `/mnt/c` if shell startup complains about UNC paths.

If Android Studio opens but Gradle/SDK state is confusing, stop and clarify whether the project should be maintained from WSL or from a Windows clone. Do not silently switch between both.

## Launch or Inspect the Windows Emulator

List Windows AVDs:

```bash
timeout 12s powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$emu="$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"; & $emu -list-avds'
```

Launch an AVD from WSL:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command 'Start-Process "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -ArgumentList @("-avd","<AVD_NAME>","-no-snapshot","-gpu","auto")'
```

Wait for boot before installing:

```bash
for i in $(seq 1 60); do
  state=$(timeout 5s "$ADB" -s emulator-5554 get-state 2>/dev/null | tr -d '\r\n')
  boot=$(timeout 5s "$ADB" -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r\n')
  printf 'try=%02d state=%s boot=%s\n' "$i" "${state:-unknown}" "${boot:-not-yet}"
  [ "$boot" = "1" ] && break
  sleep 5
done
```

## Verification

After install and launch, verify process, focus, and pixels:

```bash
"$ADB" -s emulator-5554 shell pidof com.example.game || true
"$ADB" -s emulator-5554 shell dumpsys window | rg 'mCurrentFocus|mFocusedApp'
"$ADB" -s emulator-5554 exec-out screencap -p > /tmp/phaser-android.png
file /tmp/phaser-android.png
```

Use a screenshot viewer when visual state matters. A successful install is not enough for Phaser; confirm the canvas is not blank, expected orientation is active, and touch/audio behavior is testable.

## Common Failure Modes

**PowerShell or cmd output is garbled or commands fail from `\\wsl.localhost\...`**

Run Windows commands from `/mnt/c` or another Windows filesystem directory. `cmd.exe` cannot use a UNC path as the current directory.

**`adb devices` shows no devices**

Confirm the Windows emulator is actually running, then use Windows `adb.exe`, not Linux `adb`. Restart the Windows ADB server if needed.

**Device is `offline`**

Wait for boot completion. First boot after creating an AVD can take several minutes. If it remains offline, restart the Windows ADB server and cold boot the AVD.

**Android Studio cannot comfortably open the WSL project**

Use the APK install path for app smoke tests. If native editing is needed, consider cloning or copying the repo into the Windows filesystem and keeping WSL/Windows workflows clearly separated.

**`npx cap open android` opened the wrong Android Studio**

Close that instance. Use Windows `studio64.exe` explicitly as described above, or skip Android Studio and install the WSL-built APK with Windows `adb.exe`.

**`npx cap run android` shows a target picker but launches through the wrong host**

Cancel it. Build/sync in WSL, assemble the debug APK, then install with Windows `adb.exe`. Use `"$ADB" devices -l` to choose the real Windows emulator target.
