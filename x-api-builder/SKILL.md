---
name: x-api-builder
description: "X APIを使った本番向け統合を構築する。投稿、ユーザー、いいね、ブックマーク、ストリーム、認証スコープ、フィールド展開、従量課金管理で使う。"
metadata:
  short-description: "本番向けX API統合ビルダー"
---

# X API Builder

auth mismatch、partial responses、rate limits、billing surprises など本番制約に耐える X API integration を作る。

## 考え方: Contract-First Integration

X API work は quick HTTP-call ではなく contract system として扱う。正しい integration とは、data、auth context、platform limits が変化しても正しく動くもの。

**実装前に確認すること:**

- target は REST endpoint、SDK method、またはその両方か
- その operation と fields に必要な auth context は何か
- rate window、retries、partial errors、cost model などの operational constraints は何か
- data が missing、protected、deleted、partial returned の場合どう degrade するか

**基本原則**

1. verify first, code second: current docs/OpenAPI から behavior を導き、その後に実装する
2. scope は data access: fields と expansions は見た目ではなく、permission と payload の判断
3. production over demo: retry、observability、partial-failure handling、budget awareness を最初から入れる

## ワークフロー

### 1. integration shape を定義する

- endpoint family と auth model を先に選ぶ
- business logic を書く前に required response fields と expansions を固定する
- integration が lookup、user-owned mutation、long-lived stream ingestion のどれか決める
- Posts/Users features では single-item lookup、batch lookup、write operations のどれが必要か決める
- canonical endpoint pattern の選択には `references/posts-users-playbook.md` を使う

### 2. auth と scopes を解決する

- app-only で足りるか、user-context が必須か確認する
- create post など write operations には user-context permissions と scopes が必要
- `/2/users/me` は user-context only
- user-owned Likes/Bookmarks writes では path user IDs が authenticated user と一致することを確認する
- Likes Streams では coding 前に bearer-token access と stream product entitlement を検証する
- credential families を明示する
  - OAuth 2.0 app credentials: `X_CLIENT_ID` + `X_CLIENT_SECRET`
  - OAuth 1.0a app keys: consumer key/secret。別 family
  - App-only bearer token: service token であり user login ではない
- local OAuth dev では X portal に両方の callback URL を登録する
  - `http://localhost:3000/api/x/oauth/callback`
  - `http://127.0.0.1:3000/api/x/oauth/callback`
- `redirect_uri` は authorize、token exchange、app settings で byte-for-byte identical にする
- X portal が local apps に Website URL validation を要求する場合、website metadata は `https://127.0.0.1:3000`、callback は `http` に保つ
- operation から token type を map するには `references/auth-and-scopes.md` を使う

### 3. request/response contract を設計する

- 必要な fields (`tweet.fields`, `user.fields` など) と明示的な expansions だけを request する
- batch endpoints の partial success (`data` plus `errors`) に耐える parser を作る
- missing includes を安全に扱う
- IDs は end-to-end で string として normalize する
- mutation endpoints では boolean result envelopes (`liked`, `bookmarked`) と error arrays を model 化する
- likes streams では event payload と include-aware expansions を別々に model 化する

### 4. operational guardrails を追加する

- header-driven reset handling を使い、rate-limit-aware retry を実装する
- idempotent retries と write retries を区別する。write には dedupe strategy が必要
- debugging と billing analysis に必要な request metadata を log する
- streams では reconnect + bounded backfill を実装し、valid partition ranges を強制する
- baseline limits と cost behavior には `references/rate-limits-and-billing.md` を使う

### 5. 必要に応じて TypeScript XDK に map する

- TypeScript services では official SDK methods を優先する
- method usage を endpoint semantics と合わせる
- REST-to-XDK mapping には `references/typescript-xdk-mapping.md` を使う

### 6. scenario matrix で検証する

ship 前に次を検証する。

- public object lookup success
- missing、deleted、protected object
- valid / invalid IDs が混ざった batch request
- rate-limit response と reset-aware retry path
- auth mismatch (app-only vs user-context)
- field or expansion mismatch
- path ID が authenticated user と違う user-owned endpoint
- Likes lookup cap (`/2/tweets/:id/liking_users` は lifetime max 100 users)
- `backfill_minutes` と partition bounds を伴う stream reconnection

## Output Guidance

X API features を実装するときの output には次を含める。

- endpoint または SDK method の選択と auth rationale
- fields と expansions を含む concrete request examples
- error、partial success、retry behavior
- rate limits と billing implications のメモ
- 必要なら REST と TypeScript XDK version の併記

## 避けること

**auth model なしの endpoint-first coding**

問題: 401/403 と hidden permission bugs を生み、実装後に scope mismatch が発覚する。
改善: 先に auth context、required scopes、field/expansion permissions を固定する。

**1つの OAuth flow で localhost と 127.0.0.1 を混ぜる**

問題: token exchange で redirect URI mismatch になる。
改善: 両方を登録し、1 session では片方に統一する。

**local PKCE flow で既定に HTTPS callback URL を使う**

問題: local dev server は HTTP callback endpoint が多く、HTTPS にすると callback が受けられない。
改善: 設定済みの `http://localhost:3000/...` または `http://127.0.0.1:3000/...` を使う。

**batch responses が full success と仮定する**

問題: `data` と `errors` が混在し得る。
改善: partial success と unresolved IDs を明示的に扱う。

**all fields を request する**

問題: payload bloat、permission failures、processing cost が増える。
改善: 必要 fields と expansions だけを request する。

**rate limits と billing を混同する**

問題: request limits 内でも billable resource usage で overspend し得る。
改善: request frequency と billable usage の両方を track する。

**古い pricing snippets を信頼する**

問題: X API の pricing / access は変わりやすく、古い snippets は運用判断を誤らせる。
改善: 実装時点では pricing docs と Developer Console を source of truth にする。

**posts の edit history semantics を無視する**

問題: downstream が updated content を誤処理する。
改善: `edit_history_tweet_ids` と latest version behavior を model 化する。

**すべての writes に generic retries を使う**

問題: duplicate actions や ambiguous state を生む。
改善: idempotency strategy、dedupe key、conflict handling を入れる。

**likes が永久に pageable と仮定する**

問題: `liking_users` は Post ごと lifetime 100 users cap で、full historical list にはならない。
改善: full-fidelity needs は stream / analytics pipeline へ回す。

**stream partitions を任意 knob として扱う**

問題: likes stream partitions は required で range-limited。
改善: config load 時に partitions を検証し、不正なら fail fast する。

## Variation Guidance

実装は product context で変える。

- Internal analytics backend: batch lookup、throughput、observability を最適化
- User-facing app: latency、graceful fallback、human-readable errors を優先
- Write-heavy workflows: scope checks、idempotency、conflict handling を重視
- Cost-sensitive workflows: fields/expansions を最小化し、caching と dedupe を最大化

workload shape が違うのに、1つの default stack や favorite endpoint pattern に収束させない。

## 参照

- Endpoint and payload choices: `references/posts-users-playbook.md`
- Auth decision matrix and scopes: `references/auth-and-scopes.md`
- Rate-limit and billing operations: `references/rate-limits-and-billing.md`
- TypeScript XDK mapping: `references/typescript-xdk-mapping.md`
- Implementation checklist: `references/build-workflow.md`
- Source links and verification anchors: `references/api_reference.md`

## 実行姿勢

production review に耐える integration code を作る。

- auth、rate-limit、billing risk を隠す曖昧な要求は確認する
- implicit assumptions より explicit contracts を優先する
- tradeoff を見える化し、短期的な便利さより reliability を選ぶ

## 覚えておくこと

X API integration は初回成功ではなく、変化に耐える正しさを目指す。
