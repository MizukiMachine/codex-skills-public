# Upstream notes

Repository: https://github.com/Hugo-Dz/spritefusion-pixel-snapper

Verified against upstream commit `9f1ccdf0496d0eb2e6b343b6385f4cb42cf36a36` on 2026-05-19.

The bundled wrapper uses this verified commit as its default `--ref` for reproducible behavior. Pass `--ref main` to run against the current upstream branch, or `--ref none` to leave a manually managed checkout unchanged.

Official online version: https://spritefusion.com/pixel-snapper

Purpose: snap messy/inconsistent pixel art to a perfect grid and tie colors to a strict quantized palette. The README says this is intended for AI-generated pixel art, procedural 2D art, tilemaps, isometric maps, 2D game assets, and 3D textures.

Official CLI setup:

```sh
git clone https://github.com/Hugo-Dz/spritefusion-pixel-snapper.git
cd spritefusion-pixel-snapper
cargo run input.png output.png
```

Optional color count:

```sh
cargo run input.png output.png 16
```

Optional pixel size override:

```sh
cargo run input.png output.png --pixel-size 8
```

For scripted use, prefer:

```sh
cargo run --release --manifest-path path/to/Cargo.toml -- input.png output.png 16 --pixel-size 8
```

WASM API from the README:

```js
import init, { process_image } from "./pkg/spritefusion_pixel_snapper.js";

await init();
const outputBytes = process_image(inputBytes, 16);
```

The third WASM argument is an optional pixel-size override; pass `null` for optional arguments that should use defaults.
