---
name: pixel-snapper
description: "ピクセルアートPNGをクリーンアップし、ネイティブなピクセルグリッドへ整える。擬似ピクセルアートの再ピクセル化、パレット量子化、フレーム一括処理、寸法検証で使う。"
---

# Pixel Snapper

## 目的

ピクセルアート風の raster images を、使える pixel-art assets に整える。asset に応じて hidden low-resolution grid の復元、Sprite Fusion の grid snapper、または fixed animation canvas を保った pixelate/quantize を選ぶ。

## 基本方針

pixel-art cleanup は単一操作ではない。output contract に応じて workflow を選ぶ。

| Need | Use | Output Size |
|------|-----|-------------|
| upscaled / AI-faked pixel art から native grid を復元 | `scripts/pixel_snapper.py` | source から発見 |
| known rows/columns の sheet から frames を復元 | `scripts/pixel_snapper_sheet.py` | frame ごとに発見後、再 assembly |
| single image、tile、map、texture、sample に Sprite Fusion grid snapping を使う | `scripts/spritefusion_snapper.py` | upstream 由来。既定で source aspect に pad |
| canvas size と character scale を固定して animation frames を変換 | `scripts/fixed_canvas_pixelate.py` | explicit `--size N` or `--size WxH` |
| batch dimensions、visible RGB palette、alpha behavior を検証 | `scripts/inspect_png_batch.py` | invariants に基づく report/fail |

優先順位:

1. 正しい asset contract: exploratory cleanup は native-grid discovery、game animation は fixed canvas
2. visual readability: design を保つ最小 palette
3. alpha integrity: ユーザーが hard-edged cutouts を明示しない限り soft alpha を保持
4. reproducibility: originals を残し、experiments は new output paths に書いてから採用する

## 参照ファイル

| Topic | File | Use When |
|-------|------|----------|
| Native grid recovery algorithm | [algorithm.md](references/algorithm.md) | hidden-grid recovery の debug または internal tunables 変更 |
| Native grid examples | [usage-examples.md](references/usage-examples.md) | sweeps、upscales、known-layout sheet recovery |
| Sprite Fusion upstream | [spritefusion-upstream.md](references/spritefusion-upstream.md) | exact upstream CLI、verified commit、WASM details が必要なとき |

## 開始前に確認すること

- input は fake/upscaled pixel art、already-native pixel art、continuous-tone image、game animation batch のどれか
- output size は discovery してよいか、全 frames を fixed size と stable in-game scale にする必要があるか
- single image、PNG frame folder、known rows/columns の spritesheet のどれか
- desired color count は何か。AI native-grid recovery では `256` 付近から始め、strict retro cleanup では `8`、`16`、`32` を比較する
- source が soft alpha を使っているか。使っている場合は既定で alpha levels を保持する

mode が曖昧な final batch conversion の前には短く確認する。

```text
どのトレードオフを優先しますか?
1. Native/Sprite Fusion grid-snap: 視覚的なgrid cleanupを優先。画像ごとに出力寸法が変わる場合があります。
2. Fixed-canvas animation output: すべてのframeを同じサイズに保ち、character scaleを安定させます。
3. 代表frameから比較サンプルを先に作ります。
```

ユーザーが mode、output path、size/color requirements を指定している場合や、single image で discovered output dimensions が明らかに許容される場合は質問せず進める。

## ワークフロー

1. asset と output contract を分類する。varying dimensions / offsets が許容されない限り、grid-derived batch output を final animation frames として使わない
2. source facts を記録する: file count、PNG dimensions、known sheet の rows/columns、visible alpha behavior、intended output path
3. script を選ぶ
   - fake/upscaled pixel art の hidden grid: `pixel_snapper.py`
   - known-layout sheet: `pixel_snapper_sheet.py`
   - grid-derived output が許容される Sprite Fusion cleanup: `spritefusion_snapper.py`
   - fixed-size frame batch: `fixed_canvas_pixelate.py`
4. palette size を選ぶ。不明な style は representative samples を作る
5. full batch 前に1枚または代表 frame で calibrate する
6. final conversion は new output path に実行する。source assets を上書きしない
7. workflow に合った checks で検証し、source と視覚比較する

## コマンド

AI または upscaled pixel-art PNG から hidden native grid を復元:

```bash
uv run "<skill>/scripts/pixel_snapper.py" "input.png" "output.png" --k-colors 256
```

known-layout spritesheet を復元:

```bash
uv run "<skill>/scripts/pixel_snapper_sheet.py" \
  "sheet.png" "sheet-snapped.png" --cols 4 --rows 4 --k-colors 256
```

1枚に Sprite Fusion grid snapping を実行:

```bash
python3 "<skill>/scripts/spritefusion_snapper.py" \
  --input "input.png" --output "output.png" --colors 16
```

auto-detection 失敗時だけ Sprite Fusion grid size を上書き:

```bash
python3 "<skill>/scripts/spritefusion_snapper.py" \
  --input "input.png" --output "output.png" --colors 16 --pixel-size 8
```

fixed-canvas animation frames を生成:

```bash
python3 "<skill>/scripts/fixed_canvas_pixelate.py" \
  --input-dir "input_frames" --output-dir "output_frames" --size 512 --colors 16
```

fixed-frame output batch を検証:

```bash
python3 "<skill>/scripts/inspect_png_batch.py" \
  --root "output_frames" \
  --source-root "input_frames" \
  --require-single-size \
  --max-visible-rgb 16
```

## Animation Frame Contract

character animations、frame sequences、action folders、spritesheet-derived frames では次を守る。

- source frame count と output frame count が一致する
- ユーザーが新構造を求めない限り relative paths を一致させる
- final batch conversion 前に required output frame dimensions がわかっている
- fixed-frame animation assets として使う final PNGs はすべて同じ寸法にする
- character scale は per-image visible bounds ではなく original source canvas から来る
- anchor/offset handling をユーザーが受け入れない限り visible pixels へ crop しない
- 既定で soft alpha を保持する。hard alpha は要求時のみ
- 1つの RGB color が多数の alpha levels に現れ得るため、visible RGB colors は RGBA values と別に検証する

ユーザーが "low-resolution pixel art" かつ game-ready animation frames を求めた場合、engine が deliberate per-frame offsets/anchors を持たない限り raw grid snapping より fixed-canvas pixelation を優先する。

## 検証

single-image native / Sprite Fusion output:

- output dimensions が plausible か確認する
- nearest-neighbor upscale at `x8` or `x16` で見る
- source と output を並べて比較する
- color count や grid parameters を変える場合は original source から再実行する

frame batches:

- fixed frames が必要なら `inspect_png_batch.py` に `--require-single-size` を付ける
- source/output file count と relative path parity を確認する
- visible RGB count が requested palette size 以下か確認する
- request されていない限り soft alpha が1つの opaque alpha value に collapsed していないか確認する

## 避けること

**pixel snapping を generic downscaler として使う**

問題: 写真や smooth illustration には grid-like pixel-art structure がなく、snapper は artifact を作る。
改善: pixel-art structure がある場合だけ使い、continuous-tone images には通常 resizing を使う。

**native-grid output resolution を直接指定しようとする**

問題: native grid recovery は source の hidden grid を見つける処理で、任意 resolution 指定とは別。
改善: 先に native grid を recover し、必要な倍数へ nearest-neighbor upscale する。

**raw grid-derived output を animation frames として出荷する**

問題: frame dimensions や offsets が揃わず、runtime animation jitter を起こす。
改善: dimensions と scale が必要なら fixed-canvas pixelation を使う。

**palette cleanup で alpha を flatten する**

問題: soft transparent edges が opaque halo や black fringe になる。
改善: alpha を保持し、visible RGB count を alpha levels と別に見る。

**derivative outputs を再 snap する**

問題: derivative を繰り返し snap すると detail と palette が劣化する。
改善: original source から1つの workflow を再実行し、parameters を調整する。

## トラブルシューティング

| Symptom | Likely Cause | First Fix |
|---------|--------------|-----------|
| Native output is exactly `64x64` | Hidden-grid detection fell back | Try different `--k-colors`; reject if no real grid exists |
| Output is tiny or missing detail | Palette collapsed too much signal | Increase color count |
| Output is too noisy or close to source size | Too many colors preserved edge noise | Decrease color count |
| Sprite Fusion output aspect changed | Upstream generated unequal grid counts | Keep default aspect padding; avoid `--no-preserve-aspect` |
| Animation frames vary in size | Grid-derived output was used for fixed-frame assets | Regenerate with `fixed_canvas_pixelate.py` |
| Output has dark halos | Alpha was flattened or palette used near-transparent RGB | Regenerate while preserving alpha; inspect alpha levels |
