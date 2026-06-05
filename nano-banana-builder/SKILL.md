---
name: nano-banana-builder
description: "Nano Banana/Gemini画像生成APIを使うフルスタックWebアプリを構築する。Next.jsの生成・編集・ギャラリー、APIルート、ストレージ、レート制限、本番運用で使う。"
metadata:
  short-description: "Gemini画像アプリ（Nano Banana）を構築"
---

# Nano Banana Builder

Google の Nano Banana image generation APIs を使い、simple text-to-image generators から multi-turn conversation を持つ iterative editors まで、本番向け web application を作る。

## 重要: 正確な Model Names

**次の exact model strings だけを使う。推測、date suffix 追加、独自名は禁止。**

| Model String (use exactly) | Alias | Use Case |
|---------------------------|-------|----------|
| `gemini-2.5-flash-image` | Nano Banana | fast iterations、drafts、high volume |
| `gemini-3-pro-image-preview` | Nano Banana Pro | quality output、text rendering、2K |

よくある誤り:

- `gemini-2.5-flash-preview-05-20`: text model 用 date suffix であり image generation では誤り
- `gemini-2.5-pro-image`: 2.5 Pro は direct image generation しない
- `gemini-3-flash-image`: 存在しない
- `gemini-pro-vision`: image input 用であり generation 用ではない

有効な image generation models は `gemini-2.5-flash-image` と `gemini-3-pro-image-preview` のみ。

## 考え方: Conversational Image Generation

Nano Banana は単なる image API ではなく conversational by design。image generation は one-shot prompt より dialogue として扱うと強い。

- **Iterative refinement**: 完璧な1 prompt ではなく、conversation で images を育てる
- **Context awareness**: model は previous generations / edits を覚えている
- **Natural language editing**: parameters ではなく自然言語で変更を伝える

### 実装前に確認すること

- primary use case は text-to-image generation、image editing、multi-image composition、style transfer のどれか
- model は Nano Banana (speed/iterations) か Nano Banana Pro (quality/complex prompts) か
- user journey は single generation、iterative refinement、gallery browsing のどれか
- production constraints は rate limits、storage、cost per image、user volume のどれが重要か

### 基本原則

1. **configuration より conversation**: complex parameter UI より iterative editing を活かす
2. **model selection matters**: speed/iterations は `gemini-2.5-flash-image`、quality/complexity は `gemini-3-pro-image-preview`
3. **state as conversation history**: multi-turn editing のため generations を chat messages として track する
4. **rate limit awareness**: queueing、caching、friendly errors を実装する
5. **storage strategy**: inline base64 だけでなく Vercel Blob / S3 などに generated images を保存する

### Model Selection Framework

| Use Case | Model | Why |
|----------|-------|-----|
| rapid iterations, drafts | `gemini-2.5-flash-image` | fast (2-5s)、画像あたりのコストが低い |
| final output, quality | `gemini-3-pro-image-preview` | superior quality, thinking, text rendering |
| text-heavy images | `gemini-3-pro-image-preview` | better typography, 2K resolution |
| multi-turn editing | either | both support conversational editing |
| high volume | `gemini-2.5-flash-image` | lower cost, faster throughput |

## Quick Start

### Basic Server Action

```typescript
// app/actions/generate.ts
'use server'

import { google } from '@ai-sdk/google'
import { generateText } from 'ai'

export async function generateImage(prompt: string) {
  const result = await generateText({
    model: google('gemini-2.5-flash-image'),
    prompt,
    providerOptions: {
      google: {
        responseModalities: ['IMAGE'],
        imageConfig: { aspectRatio: '16:9' }
      }
    }
  })

  return result.files[0] // { base64, uint8Array, mediaType }
}
```

### `useChat` Client Component

```typescript
// app/components/ImageGenerator.tsx
'use client'

import { useChat } from '@ai-sdk/react'

export function ImageGenerator() {
  const { append, messages, isLoading } = useChat({
    api: '/api/generate'
  })

  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          {m.parts?.map((part, i) =>
            part.type === 'image' && (
              <img key={i} src={part.url} alt="Generated" />
            )
          )}
        </div>
      ))}

      <button
        disabled={isLoading}
        onClick={() => append({
          role: 'user',
          content: 'A futuristic cityscape at dusk'
        })}
      >
        Generate
      </button>
    </div>
  )
}
```

## Advanced Implementation

complete implementations は `references/advanced-patterns.md` を読む。

- Server Actions: model selection、storage、error handling
- API Routes: streaming responses
- Client Components: iterative editing、galleries
- Advanced Patterns: multi-image composition、batch generation

## Configuration & Operations

詳細は `references/configuration.md` を読む。

- Provider Options: responseModalities、imageConfig、thinkingConfig
- Storage Strategy: Vercel Blob、S3/R2 implementations
- Rate Limiting: Upstash Redis patterns、quota management
- Cost Optimization strategies

## 避けること

**model names を作る、date suffix を足す**

問題: 存在しない model string は API failure を起こし、debug を誤誘導する。
改善: documented exact strings だけを使う。

**Gemini 2.5 Pro を images に使う**

問題: Gemini 2.5 Pro は direct image generation 用ではない。
改善: image generation には `gemini-2.5-flash-image` または `gemini-3-pro-image-preview` を使う。

**DB に base64 だけ保存する**

問題: blob database、expensive storage、slow retrieval になりやすい。
改善: object storage (Vercel Blob/S3) に保存し、DB には URL だけ持つ。

**rate limit handling がない**

問題: production で 429 と悪い UX を生む。
改善: rate limiting を実装し、user-friendly な error messages を出す。

**multi-turn context を無視する**

問題: Nano Banana の conversational editing の強みを捨て、small edits が drift しやすくなる。
改善: iterative refinement のため chat history を track する。

**client-side に API key を hardcode する**

問題: key leakage と unauthorized spend を招く。
改善: server actions / API routes と environment variables を使う。

**wrong aspect ratio**

問題: use case と違う aspect ratio は crop、layout、social preview、mobile UI で破綻する。
改善: intended use case に合わせて aspect ratio を選ぶ。

**loading states がない**

問題: generation は 5-30s かかることがあり、UI が止まったように見える。
改善: progress indicators、estimated wait time、cancel/retry affordance を出す。

**every keystroke で生成する**

問題: quota を浪費し、latency と cost を増やす。
改善: debounce し、explicit generate action を要求する。

## Variation Guidance

app は目的に合わせて設計する。

- **UI Style**: minimal、brutalist、playful、professional、dark、light
- **Color Scheme**: warm、cool、monochrome、vibrant、muted
- **Layout**: single page、multi-step wizard、sidebar、grid、list
- **Interaction**: click-to-generate、drag-and-drop、real-time typing、batch

避ける overused patterns:

- default Tailwind purple gradients
- generic "AI startup" aesthetic
- every project で同じ component libraries
- 意図のない Inter / Roboto fonts

context で design を決める。

- Meme generator -> bold, fun, casual
- Product mockup tool -> clean, professional, grid-based
- Art exploration -> gallery-first, visual-heavy
- Brand asset creator -> polished, template-guided

## Environment Setup

```bash
# .env.local
GEMINI_API_KEY=your_api_key_here

# For Vercel Blob storage
BLOB_READ_WRITE_TOKEN=your_vercel_token

# For S3 (optional)
S3_BUCKET=your-bucket
S3_ENDPOINT=https://your-endpoint.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your_key
S3_SECRET_ACCESS_KEY=your_secret

# For Upstash rate limiting (optional)
UPSTASH_REDIS_REST_URL=your_url
UPSTASH_REDIS_REST_TOKEN=your_token
```

```bash
# Install dependencies
npm install @ai-sdk/google ai @ai-sdk/react @vercel/blob

# Or if using separate packages
npm install google-genai
```

## 覚えておくこと

Nano Banana は creative partner と作業するような conversational image generation を可能にする。best apps は multi-turn editing を活かし、model を意図して選び、rate limits を graceful に扱い、images を効率よく保存し、良い loading states を備え、目的に合う独自の体験として設計されている。
