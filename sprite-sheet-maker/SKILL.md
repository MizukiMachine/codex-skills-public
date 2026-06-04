---
name: sprite-sheet-maker
description: "複数のフレームPNGをゲーム用スプライトシートにまとめる。番号付きフレーム、ピクセルアート、キャラクターアクション列、4x4配置などで使う。"
---

# Sprite Sheet Maker

## 目的

同梱の `scripts/make_spritesheet.py` で、複数の PNG アニメーションフレームを1枚のスプライトシートへまとめる。スクリプトは pure Python で、Pillow、ImageMagick、npm package は不要。

## ワークフロー

1. 指定された input directory と output path を使う。どちらかが不明なときだけ確認する
2. 既定では自然順で並べる。`frame_2.png` が `frame_10.png` より前に来る
3. ユーザーが layout を指定しない限り、正方形に近い grid を使う。16 frames は `4x4`
4. 透明度を保持し、既定では透明背景にする
5. 可変サイズの character frame は `--align bottom-center` を維持し、足元や baseline の揺れを減らす。icon や effect では `--align center` を使う
6. engine integration で frame rectangle や source offset が必要なら JSON metadata を生成する

## クイックコマンド

既定のスプライトシート:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png"
```

4 columns に固定し、PNG の隣に metadata を書く:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png" --columns 4 --metadata
```

固定 cell、center alignment、spacing を使う:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png" --columns 4 --cell-width 256 --cell-height 256 --align center --spacing 2
```

書き込まずに出力計画を確認する:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png" --dry-run
```

## スクリプトの挙動

- 入力: non-interlaced 8-bit PNG。RGBA、RGB、grayscale、grayscale-alpha、indexed-color に対応
- 出力: 8-bit RGBA PNG
- 既定 cell size: 全 input frame の最大 width/height
- 既定 grid: `ceil(sqrt(frame_count))` columns と必要な rows。16 frames は `4x4`
- 既定 order: natural filename order
- 既定 alignment: `bottom-center`
- 既定 margin/spacing: `0`
- 既定 background: transparent

## オプション

- `--pattern "*.png"`: `--input-dir` 内の対象ファイルを選ぶ
- `--columns N` / `--rows N`: grid layout を制御する
- `--cell-width N` / `--cell-height N`: cell dimensions を固定する。最大 frame より小さい cell は拒否される
- `--align VALUE`: `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right` のいずれか
- `--margin N`: 外側 margin pixels
- `--spacing N`: cell 間 spacing pixels
- `--background transparent|#RRGGBB|#RRGGBBAA`: 背景塗り
- `--metadata [path]`: JSON metadata を書く。path なしなら `<output>.json`
- `--order natural|lex`: filename sort を選ぶ

## トラブルシューティング

- アニメーションが予想外に揺れる: character は `--align bottom-center`、effect は `--align center` で再実行する
- output cell が大きすぎる: source frame dimensions を確認する。可変サイズ frame は最大 frame size が cell size になる
- engine が1行を期待する: `--columns <frame-count>` または `--rows 1` を使う
- engine が正確な cell size を期待する: `--cell-width` と `--cell-height` を渡す
- unsupported PNG error: source frames を non-interlaced 8-bit PNG に変換してから実行する
