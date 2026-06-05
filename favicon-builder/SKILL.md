---
name: favicon-builder
description: "Webサイトやアプリ向けのfavicon・PWAアイコン一式を生成する。既存ブランドに合わせた差し替え、ブラウザプレビュー、フレームワークのメタデータ更新で使う。"
metadata:
  short-description: "favicon一式を生成"
---

# Favicon Generator

## できること

app の既存 brand identity に合う production-ready favicon suite を作る。PNG、ICO、SVG assets を生成し、実際の browser size で preview し、Next.js `metadata.icons` や標準 HTML `<link>` tags など framework metadata を更新できる。

## 参照ファイル

| Topic | File | Use When |
|-------|------|----------|
| Rendering effects | [references/effects-guide.md](references/effects-guide.md) | shadow、glow、highlight、noise、scaling、color handling の実装詳細が必要なとき |
| Python generator | [scripts/generate_favicon.py](scripts/generate_favicon.py) | project directory または CI-friendly な deterministic files が必要なとき |
| Browser studio | [scripts/generate_favicon.html](scripts/generate_favicon.html) | quick visual exploration、manual tuning、side-by-side previews が必要なとき |

## 基本方針

favicon は小さな brand artifact で、ただの装飾ではない。優先順位は次の通り。

1. project の実際の brand mark、icon library、colors に合わせる
2. 16px と 32px でも読めるようにする
3. subtle layered effects で polish を足す
4. complete asset set を生成し、app に wiring する

既存 logo/icon があるならそれを使う。brand icon がない場合は、product の機能と audience に合う simple letter、Lucide icon、emoji を選ぶ。

## まず調査する

生成前に対象 project を確認する。

```bash
rg "from.*lucide-react|from.*@lucide" --type ts --type tsx
rg "Logo|Header|Nav|Brand|Icon" --type ts --type tsx
rg "favicon|apple-touch-icon|manifest|metadata" .
rg "primary|brand|--.*color|themeColor" .
```

確認するもの:

- 既存 logo または brand icon
- 現在の favicon files と public assets の配置先
- CSS variables、Tailwind config、theme files、design tokens 由来の brand colors
- icon metadata を置く framework entry point

コードベースに recognizable brand mark がある場合、generic icon を作らない。

## 生成方法

最終 project assets には CLI を使う。

```bash
python3 /home/mizuki2/.codex/skills/favicon-builder/scripts/generate_favicon.py \
  --letter A --style modern --output ./public

python3 /home/mizuki2/.codex/skills/favicon-builder/scripts/generate_favicon.py \
  --lucide rocket --style vibrant --output ./public

python3 /home/mizuki2/.codex/skills/favicon-builder/scripts/generate_favicon.py \
  --letter N --bg "#0f172a" --bg2 "#1e293b" --fg "#22d3ee" \
  --shadow 0.5 --highlight 0.3 --glow 0.2 --noise 0.04 \
  --radius 0.22 --output ./public
```

Dependencies:

```bash
python3 -m pip install Pillow
# Lucide rendering also needs:
python3 -m pip install cairosvg
```

local Python に `pip` がない、または isolated one-off run をしたい場合は `uv` を使う。

```bash
uv run --with Pillow --with cairosvg python \
  /home/mizuki2/.codex/skills/favicon-builder/scripts/generate_favicon.py \
  --lucide rocket --style vibrant --output ./public
```

visual iteration が重要なときは browser studio を使う。

```bash
xdg-open /home/mizuki2/.codex/skills/favicon-builder/scripts/generate_favicon.html
```

## Templates

| Template | Character | Good For |
|----------|-----------|----------|
| `modern` | clean indigo/purple | SaaS and productivity |
| `vibrant` | energetic pink/orange | consumer and social apps |
| `minimal` | dark and restrained | developer tools and utilities |
| `glass` | blue/cyan with shine | dashboards and analytics |
| `neon` | dark with cyan glow | games and creative tools |
| `warm` | amber/red | food, lifestyle, community |
| `forest` | green/teal | health, environment, finance |
| `mono` | black/white | neutral or adaptable brands |

Built-in Lucide icons:

`package-plus`, `rocket`, `zap`, `star`, `heart`, `code`, `box`, `compass`, `flame`, `globe`, `layers`, `music`, `send`, `shield`, `sparkles`, `sun`, `target`, `terminal`, `wand`

project が built-in ではない Lucide icon を使っている場合は、`node_modules/lucide-react/dist/esm/icons/<icon-name>.js` から SVG path elements を読み、generator に one-off entry を追加するか、project-specific script を作る。

## 出力契約

CLI は次を書き出す。

```text
output/
├── favicon.ico
├── favicon.svg
├── favicon-16x16.png
├── favicon-32x32.png
├── favicon-48x48.png
├── favicon-64x64.png
├── favicon-128x128.png
├── apple-touch-icon.png
├── favicon-192x192.png
└── favicon-512x512.png
```

framework が別の場所を要求しない限り、app の public/static asset directory に置く。

## Integration

Next.js App Router:

```typescript
// app/layout.tsx
export const metadata = {
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180" }],
  },
};
```

HTML:

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
```

PWA manifest:

```json
{
  "icons": [
    { "src": "/favicon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/favicon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

## 品質確認

- `favicon-16x16.png` と `favicon-32x32.png` を確認し、mark が潰れるなら単純化する
- 生成 file が framework の served asset directory にあるか確認する
- metadata または link tags が生成 paths を指しているか確認する
- project に brand tokens がある場合は default template colors より brand colors を優先する
- noise と glow は subtle に保ち、polish 以上の視覚ノイズにしない

## 避けること

- 理由なく real brand icon を generic monogram に置き換える
- 512px icon だけを生成し、browser-tab sizes を省く
- large-preview icon が 16px でも機能すると仮定する
- project に定義色があるのに arbitrary blue/purple gradients を使う
- favicon integration 中に無関係な branding/layout files を更新する
