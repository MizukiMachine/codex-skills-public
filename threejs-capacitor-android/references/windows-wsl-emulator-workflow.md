# WSL2 Project with Windows Android Emulator

Use this when the project lives in WSL2/Linux but Android Studio, `adb.exe`, or the emulator should run on Windows. This is common when a WSL2 emulator boots but its side toolbar, rotation, home, back, or power controls are unreliable.

## Decision Rule

Prefer the WSL-built APK plus Windows `adb.exe` when:
- the APK already builds in WSL
- the goal is to run or smoke-test the app
- the app changes are mostly TypeScript, Three.js, CSS, assets, Capacitor config, or Android manifest values already synced
- Windows Android Studio/Gradle setup is unknown or would add friction

Prefer Windows Android Studio when:
- the user needs Gradle sync UI, Logcat, profilers, Device Manager, or manifest/resource editors
- native Android code or Gradle files are the main work
- the project will be maintained primarily from Windows

Avoid opening a WSL UNC path in Windows tools as the first move unless the user explicitly wants that workflow. UNC paths can be slower and some command-line tools start in `\\wsl.localhost\...`, which `cmd.exe` does not support as a current directory.

## Discovery Checklist

From WSL project root:

```bash
sed -n '1,220p' package.json
sed -n '1,220p' capacitor.config.*
npm run android:doctor
test -f android/app/build/outputs/apk/debug/app-debug.apk && stat android/app/build/outputs/apk/debug/app-debug.apk
```

From WSL, query Windows from a Windows filesystem working directory such as `/mnt/c` to avoid UNC-current-directory problems:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$ErrorActionPreference="SilentlyContinue"; foreach ($name in "adb.exe","emulator.exe","studio64.exe") { $cmd = Get-Command $name; if ($cmd) { "$name=$($cmd.Source)" } else { "$name=NOT_IN_PATH" } }'

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$paths = @("$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe", "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe", "$env:ProgramFiles\Android\Android Studio\bin\studio64.exe"); foreach ($p in $paths) { if (Test-Path $p) { "FOUND=$p" } else { "MISSING=$p" } }'
```

If Windows SDK tools are not on PATH, use the default full paths. Do not assume PATH is configured.

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
"$ADB" -s emulator-5554 shell am start -n com.example.app/.MainActivity
```

Find the real package and activity when uncertain:

```bash
"$ADB" -s emulator-5554 shell cmd package resolve-activity --brief com.example.app
"$ADB" -s emulator-5554 shell pm list packages | rg 'example|appname'
```

Use one ADB host consistently. If device state looks stale, restart the Windows ADB server:

```bash
"$ADB" kill-server
"$ADB" start-server
"$ADB" devices -l
```

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

## AVD and System Image Setup

Best default: create a Windows AVD in Android Studio Device Manager and download a Google APIs x86_64 system image there.

If Android Studio exists but no Windows AVD is listed:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$emu="$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"; & $emu -list-avds'
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command 'Get-ChildItem "$env:LOCALAPPDATA\Android\Sdk\system-images" -Recurse -Filter package.xml -ErrorAction SilentlyContinue | ForEach-Object { $_.DirectoryName }'
```

Copying a system image from WSL to Windows can work as a pragmatic recovery path, but it is a multi-GB SDK mutation. Prefer Android Studio's SDK Manager unless the user wants the fastest local fix and there is enough disk space.

## Verification

After install and launch, verify process, focus, and pixels:

```bash
"$ADB" -s emulator-5554 shell pidof com.example.app || true
"$ADB" -s emulator-5554 shell dumpsys window | rg 'mCurrentFocus|mFocusedApp'
"$ADB" -s emulator-5554 exec-out screencap -p > /tmp/android-app.png
file /tmp/android-app.png
```

Use a screenshot viewer when visual state matters. A successful install is not enough for Three.js; confirm the screen is not blank and the expected orientation is active.

## Common Failure Modes

**PowerShell or cmd output is garbled or commands fail from `\\wsl.localhost\...`**

Run Windows commands from `/mnt/c` or another Windows filesystem directory. `cmd.exe` cannot use a UNC path as the current directory.

**`adb devices` shows no devices**

Confirm the Windows emulator is actually running, then use Windows `adb.exe`, not Linux `adb`. Restart the Windows ADB server if needed.

**Device is `offline`**

Wait for boot completion. First boot after creating an AVD can take several minutes. If it remains offline, restart the Windows ADB server and cold boot the AVD.

**`monkey` fails during first boot because Google services are busy**

Wait, then start the activity explicitly with `am start -W -n <package>/.MainActivity`.

**Android Studio cannot comfortably open the WSL project**

Use the APK install path for app smoke tests. If native editing is needed, consider cloning or copying the repo into the Windows filesystem and keeping WSL/Windows workflows clearly separated.
