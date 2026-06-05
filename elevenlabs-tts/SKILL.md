---
name: elevenlabs-tts
description: "ElevenLabsの音声読み上げをNode/Python/Webアプリに統合する。認証、音声・モデル選択、ストリーミング、バッチ生成、レイテンシ対策で使う。"
metadata:
  short-description: "ElevenLabs TTS実装フレームワーク"
---

# ElevenLabs TTS

production code に ElevenLabs text-to-speech を実装または debug するときに使う。API 使用法より先に、architecture decision を固める。

## 考え方: 音声はプロダクト体験

TTS は単なる API call ではない。identity、latency、intelligibility、reliability にまたがる UX contract として扱う。

**実装前に確認すること:**

- interaction は realtime、near-realtime、offline pre-generation のどれか
- 最重要なのは naturalness、speed、cost、deterministic reproducibility のどれか
- trust boundary はどこで、API credentials をどう守るか
- voice generation が失敗または timeout したとき、何に fallback するか

**基本原則**

1. Delivery-first design: pipeline と endpoint は好みではなく latency/quality target から選ぶ
2. Secrets never in clients: API keys は server-side。client には必要時だけ short-lived scoped tokens を渡す
3. Deterministic contracts: retries と caching が安全になるよう request/response shape を標準化する
4. Graceful degradation: ship 前に timeout、retry、fallback を定義する

## 使う場面

- ElevenLabs API quickstart/authentication
- Node.js、Python、browser、mobile wrapper での text-to-speech generation
- `voice_id`、`model_id`、`output_format`、latency strategy の選択
- local demo から production-safe architecture への移行
- clipping、不自然な cadence、遅い response time の改善

## 判断フレームワーク

### 1. generation mode を選ぶ

- Batch generation: narration、static prompts、cutscenes、reusable assets に向く
- Streaming generation: time-to-first-audio が重要な conversational UX に向く
- Hybrid: common lines は pre-generate し、dynamic lines だけ stream する

### 2. quality / latency strategy を選ぶ

- responsiveness 優先: lower-latency path と smaller payloads
- quality 優先: higher-quality models と post-process/caching
- repeatability 優先: model/version を pin し、content hash で cached assets を再利用

### 3. integration boundary を選ぶ

- Server-generated audio (推奨既定): backend が ElevenLabs を呼び、audio URL/bytes を返す
- Tokenized client access: backend が constrained client-side calls 用に short-lived token を mint する
- Offline pipeline: content build step で static/public assets へ files を生成する

## 実装ワークフロー

### 1. 明示的な contract を定義する

stable input model の例:

- `text`
- `voiceId`
- `modelId`
- `outputFormat`
- 任意の tuning fields。product が必要なものだけ

stable output model の例:

- `audioUrl` または base64/blob reference
- `mimeType`
- `durationMs`。わかる場合
- `cacheHit`

### 2. 安全な API access を作る

- key は environment variable (`ELEVENLABS_API_KEY`) に保存する
- frontend bundle に key を hardcode / ship しない
- direct-client pattern では backend から short-lived, minimally scoped token を mint する

### 3. retries と fallback を実装する

- transient failures は短く bounded backoff で retry する
- request timeout を設定し、UX context に対して十分早く fail する
- fallback は cached previous audio、backup voice/model、text-only UX などから選ぶ

### 4. caching を意図的に追加する

- cache key: normalized text + voice + model + output format の hash
- 可能なら immutable audio URLs を使う
- voice/model または normalization rules が変わったときだけ cache bust する

### 5. perceptual checks で検証する

- names/domain terms の pronunciation
- clipping、pacing、sentence boundary pauses
- mobile / slow network の挙動

## 避けること

**frontend code に API key を置く**

問題: key leakage と account abuse の risk がある。
改善: privileged calls は backend または token broker 経由にし、key は environment variable に保存する。

**すべて同じ voice settings にする**

問題: alerts、narration、dialogue で同じ tuning を使うと不自然になる。
改善: use-case ごとに preset を持ち、voice stability / similarity / style を用途に合わせる。

**timeout / fallback がない**

問題: network や synthesis が遅いと UX が詰まり、flow が脆くなる。
改善: strict timeout と deterministic fallback を置く。

**同一 text を繰り返し regenerate する**

問題: cost と latency の無駄が増える。
改善: normalized text、voice id、settings、model を含む content-hash caching を使う。

**latency と quality tuning を混ぜる**

問題: 何が改善または悪化したか測定できない。
改善: 1変数ずつ、latency、MOS/subjective rating、error rate など明示 metric で test する。

## Variation Guidance

**IMPORTANT**: 実装は product context に合わせて変える。

- voice persona は narrator、assistant、NPC、system alert など role ごとに変える
- output format は web streaming、downloadable assets、mobile playback constraints で変える
- fallback policy は feature criticality で変える
- chunking strategy は long-form text と short conversational lines で変える

単一の default voice/model に収束させない。

## 参照

- API patterns and endpoint selection: `references/api-patterns.md`

## 覚えておくこと

speech pipeline は UX と operational constraints から設計する。API call は簡単な部分で、production behavior が本題。

Codex はこの領域で非常に優れた仕事ができる。これらの原則を使って、より良い判断を引き出し、context に適応し、堅牢な voice experience を ship する。
