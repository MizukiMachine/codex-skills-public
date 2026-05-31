# Three.js Animation Index Pattern

This layer is shared across browser, iOS, and Android because it is pure Three.js/web code.

## Purpose

Decouple UI and state logic from raw GLB clip names by using a JSON index contract. This prevents renamed or swapped animation files from silently breaking runtime controls.

## Contract Shape

Use a character entry with:
- `skeleton.url`
- `animationSource.url`
- `animations[]`
  - `id`
  - `displayName`
  - `sourceClipName`
  - `loop`
  - optional `fadeInSec`, `fadeOutSec`, `timeScale`
- `defaults.defaultAnimationId`
- `defaults.crossFadeSec`

Example:

```json
{
  "characters": {
    "hero": {
      "skeleton": { "url": "/assets/hero/hero.glb" },
      "animationSource": { "url": "/assets/hero/animations.glb" },
      "defaults": {
        "defaultAnimationId": "idle",
        "crossFadeSec": 0.18
      },
      "animations": [
        {
          "id": "idle",
          "displayName": "Idle",
          "sourceClipName": "Idle",
          "loop": "repeat"
        },
        {
          "id": "jump",
          "displayName": "Jump",
          "sourceClipName": "Jump",
          "loop": "once",
          "fadeInSec": 0.08,
          "fadeOutSec": 0.12
        }
      ]
    }
  }
}
```

## Runtime Pattern

1. `fetch('/assets/assets_index.json')`
2. Resolve `characters[characterId]`.
3. Load skeleton GLB with `GLTFLoader`.
4. Load animation GLB with `GLTFLoader`.
5. Build `AnimationMixer` from the skeleton root.
6. For each `animations[]` entry:
   - find `AnimationClip` by exact `sourceClipName`
   - create one reusable `AnimationAction`
   - apply loop mode, clamp, and time scale
   - register UI control by stable `id`
7. Start `defaults.defaultAnimationId`.

Keep `.glb`, textures, and JSON under `public/assets/` so Vite copies them verbatim into `dist/` and Capacitor ships them in the APK/AAB assets.

## Required Assertions

At startup, validate:
- index JSON loaded successfully
- target character exists
- `animations[]` is non-empty
- every `sourceClipName` resolves to a clip
- every `id` is unique
- default animation id exists, or a safe fallback is selected with a warning

Fail loudly with clear messages for contract errors. Do not let missing clips degrade into buttons that do nothing.

## Loop Mode Mapping

Map string loop values to Three.js constants:
- `repeat` -> `THREE.LoopRepeat`
- `once` -> `THREE.LoopOnce` and `action.clampWhenFinished = true`
- `pingpong` -> `THREE.LoopPingPong`

For `once` clips, decide what happens after finish:
- return to default animation
- hold final pose
- emit a state event for gameplay/UI

Make this behavior explicit rather than burying it in a click handler.

## UI Rule

Generate animation controls from JSON, not hardcoded arrays. This keeps UI, clip names, defaults, and transitions aligned with asset updates.

For QA tools, expose diagnostics:
- available clip names
- unresolved `sourceClipName` entries
- clip durations
- active action id
- loaded asset URLs
