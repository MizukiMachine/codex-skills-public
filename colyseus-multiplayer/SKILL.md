---
name: colyseus-multiplayer
description: "Colyseusでサーバー権威型のマルチプレイヤーゲームを構築する。ルーム設計、Schema状態同期、マッチメイキング、再接続、認証、デプロイ、Webクライアント統合で使う。"
metadata:
  short-description: "Colyseusの設計、状態同期、デプロイ、エンジン統合"
---

# Colyseus Multiplayer

Colyseus で realtime multiplayer games を設計・実装する。networking model を特定 renderer に結合しない。

## 考え方: Authority First, Rendering Second

Colyseus は server が truth を所有し、client が intent を表現するときに強い。room は local game loop の transport wrapper ではなく、公平性、一貫性、reconnect recovery が必要な部分の game loop。

multiplayer の guiding question は「frontend を websocket で mirror する方法」ではなく、「この fact はなぜ authoritative であるべきか、client が理解して render できる最小の server-owned model は何か」。

**構築前に確認すること:**

- authoritative state と cosmetic state の境界
- room boundary は match、lobby、shard、encounter のどれか
- client messages は player intent か、server だけが出すべき fact か
- late joins、reconnects、spectators、disconnects の扱い
- latency strategy: interpolation、client prediction、prediction + reconciliation

**基本原則**

1. server owns truth: movement、combat、timers、win conditions、inventory、room membership は client trust に依存させない
2. shared state stays minimal: scene graph / renderer state ではなく durable game facts を sync
3. channels を分ける: schema state は durable world state、messages は intent / transient events、cosmetics は local code
4. recovery は feature の一部: reconnect、validation、throttling、auth を最初から設計する
5. renderer は downstream: Phaser、Three.js、PixiJS、React は同じ room model に adapt する

## 参照ファイル

作業領域に応じて先に読む。

| Working on | Read first |
|------------|------------|
| Room design、schema modeling、message boundaries、lifecycle hooks、matchmaker | `references/architecture.md` |
| TypeScript client、`Callbacks`、join methods、messages、reconnection、prediction | `references/client.md` |
| review / anti-patterns | `references/anti-patterns.md` |
| production topology、Vercel frontend + backend、env vars、auth、rollout | `references/deployment.md` |
| renderer integration | `references/frameworks/README.md` |
| Phaser integration | `references/frameworks/phaser.md` |

Phaser client でなければ Phaser reference は skip し、renderer adapter は薄く保つ。

## 使う場面

- Colyseus で new multiplayer game を設計する
- Phaser、Three.js、PixiJS、React、custom web game に netplay を追加する
- schema state と message の境界を決める
- desync、reconnect、join failure、late join を debug する
- matchmaking、room topology、deployment を計画する
- authority mistakes、renderer coupling、scaling risk を review する

## Quick Decision Guide

| Question | Answer | Where to look |
|----------|--------|---------------|
| この fact はどこに置くべきか | reconnect / late join が必要なら通常 room schema state | `references/architecture.md` |
| client は state changes にどう反応するか | `Callbacks` の `listen`、`onAdd`、`onRemove` | `references/client.md` |
| players は action をどう trigger するか | `room.send(type, payload)` で intent を送り、server-side で validate | `references/client.md` |
| action SFX/VFX はいつ play するか | room が action を accept、または transient event を broadcast した後が基本 | `references/architecture.md` と必要な renderer reference |
| focus return 後に SFX/VFX が遅れて burst する場合はどうするか | inactive 中の cosmetic feedback は droppable として扱い、hidden-tab effects を durable state のように replay しない | `references/client.md` と必要な renderer reference |
| combat timing と animation をどう揃えるか | action は schema で開始し、hit/damage は authoritative active frame/window で resolve | `references/architecture.md` |
| disconnect からどう recover するか | `onDrop()`、`allowReconnection()`、client reconnect flow | `references/architecture.md` と `references/client.md` |
| bad multiplayer habits をどう避けるか | design / review 中に anti-pattern checklist を使う | `references/anti-patterns.md` |
| Vercel frontend とどう host するか | static frontend と always-on realtime backend を分離 | `references/deployment.md` |
| Phaser をどう wire するか | thin adapter と scene-safe listener lifecycle を使う | `references/frameworks/phaser.md` |

## Working Model

- `Room`: multiplayer session の authoritative boundary
- `Schema`: clients が subscribe する shared world model
- `room.send()` / `onMessage()`: client intent と server command handling
- `broadcast()`: durable state に置かない transient events
- `setSimulationInterval()`: fixed server-side update loop
- `onDrop()` / `allowReconnection()` / `onReconnect()`: recovery behavior
- `matchMaker`: room creation、search、seat reservation、stats
- `onAuth()` / `client.auth.token`: trust boundary

## Design Workflow

### 1. Define the room boundary early

- room が lobby、match、raid instance、social hangout、shard のどれを表すかを決める
- players が `joinOrCreate`、`join`、`joinById`、server-reserved seat のどれで参加するかを決める
- create、invite、reconnect、spectate、leave、rematch の player flows から設計する

### 2. Separate state, intent, and cosmetics

- durable world facts は schema state に置く: mattering entity positions、health、cooldowns、timers、ownership、score、round phase
- player requests は messages に置く: move、aim、cast、ready、interact、select loadout
- purely visual behavior は client に置く: camera shake、interpolation、particles、audio、screen flashes、local anticipation

### 3. Model schema by identity, not by presentation

- frequently shifting arrays より stable entity IDs と keyed collections を優先する
- schema shape は scene node hierarchy ではなく game rules に近づける
- canonical values を保存する。derived display values は通常 client-side で計算する
- reconnects や late joiners に必要な facts は schema fields にする

### 4. Simulate on the server

- authoritative simulation は通常 fixed tick で room から実行する
- incoming message は適用前に必ず validate する
- local prediction が diverge したら clients を correct する
- abusive message rates を throttle し、impossible actions を reject する

### 5. Plan failure paths before polish

- dropped player を disconnected として in-state に残すか、すぐ remove するかを決める
- match を pause するか、AI を substitute するか、continue するかを決める
- seat reservations と reconnect windows の長さを決める
- user-visible errors と operational errors を分ける

### 6. Deploy it like a backend, not like a static site

- Colyseus は always-on realtime service として扱う
- web client は Vercel など任意の場所で host してよいが、Colyseus server は long-lived websocket connections 向け infrastructure に置く
- URL、TLS、auth token strategy、region choice、observability、graceful shutdown を explicit にする

### 7. Add a runtime-debug surface early

- production rollout 前に小さな `/health` route を追加する
- `/health` で次を報告する
  - service liveness
  - protocol version
  - build label
  - critical runtime envs が process から実際に見えているか
- 次を明確に区別する
  - dashboard env state
  - deployed git revision
  - active process runtime state
- platform behavior が曖昧なら、UI や deployment dashboard から推測せず explicit health/debug fields と targeted log lines を追加する

### 8. Treat analytics and replay as authoritative backend concerns

- analytics は browser telemetry ではなく accepted server intents と authoritative outcomes から emit する
- summary analytics と replay storage を分ける
- exact replay では position sampling だけでなく次を優先する
  - input/event logs
  - periodic authoritative snapshots
- sink activation の observable confirmation を追加する
  - analytics sink enabled
  - first match/session write attempt
- final checkpoints は match end で一度だけ force する。simulation tick ごとに throttle を bypass しない

### 9. Keep asset/body/render contracts explicit

- multiplayer server が bodies を simulate し、client が sprites を render する場合は explicit anchor contract を定義する
- authoritative state から render されるすべての entities に `feetLine` や `contactY` など first-class metadata を優先する
- single-player と multiplayer で次を揃える
  - collision box semantics
  - contact point semantics
  - facing/direction semantics
- multiplayer が tile bodies ではなく simplified collision geometry を使う場合、その geometry を real level data と同期させる。そうしないと drift が起きる

### 10. Separate accepted actions from visual anticipation

- client input は request として扱い、action が起きた保証とはみなさない
- one-shot actions では sequence counters または transient messages を使い、clients が animations を意図的に restart できるようにする
- local SFX/VFX は accepted room state で gate する。特に `waiting`、`countdown`、cooldown、stun、death など non-controllable states
- melee や timed attacks では attack action を即座に set し、hit/damage は server-owned active frame/window で後から resolve する
- round reset、finish、player leave 時には pending attacks、casts、delayed effects を clear する

### 11. Treat transient feedback as droppable cosmetics

- durable results は schema または authoritative messages に置く。audio、hit flashes、screen shake、particles は browser inactivity 後に guaranteed replay しなくてよい
- browser clients では hidden / unfocused tabs が timers/audio を pause し、resume 時に misleading burst を起こすことがある。document hidden / unfocused 中は non-critical gameplay SFX/VFX を queue せず skip する
- visibility/focus return 時は current room state から presentation を rebuild する。product が event log を明示的に必要としない限り、missed transient event をすべて replay しない
- delayed / bursty effects を debug するときは、event type、room/session IDs、local player ID、phase、winner/result state、timestamp、document visibility/focus state、cue name、requested volume、played/skipped を log する
- countdowns や movement は sampling しない限り per-tick logs を避ける。state transitions と accepted/rejected one-shot events を log する

## Deployment Playbook

small web games の default shape:

- static frontend on Vercel など
- always-on Colyseus backend on Colyseus Cloud など persistent Node host
- persistence/analytics は必要なら room server と分離

Colyseus Cloud checklist:

- GitHub deploy key/app access
- backend package の `build` script
- `ecosystem.config.cjs` など valid PM2 file
- runtime env が Cloud dashboard に設定済み
- deploy 後に health endpoint を確認

Vercel/static frontend checklist:

- plain static files なら hosting のためだけに Vite を入れない
- repo shape が曖昧なら output directory を明示
- raw `/src/*` modules / public runtime config の cache headers を管理

Convex/analytics checklist:

- Convex prod functions が実際に deployed されている
- authoritative server と Convex deployment が同じ ingest key を共有している
- first writes は match end だけでなく room creation / join 時点でも確認する

general lessons:

- frontend が plain static site なら、hosting defaults に合わせるだけの bundler migration は不要。本当に build system が必要な場合だけ追加する
- frontend public runtime config を明示する
- browser code が private hosting env vars を自動で読めると仮定しない
- Cloud deploy は current local working tree ではなく pushed repository state を使うと想定する
- configured env vars、deployed revision、active runtime process state を区別する
- health endpoints と first-write logs で active process を証明する

## 避けること

**client-authoritative gameplay**

問題: browser は改ざん可能で、movement、hit、score、item ownership を信頼すると fairness が壊れる。
改善: server が truth を持ち、client は intent だけを送る。

**renderer を schema state に詰める**

問題: sprite flip flags、animation frame index、camera settings などは network truth ではなく local presentation。
改善: schema state には durable game facts だけを置く。

**messages をすべての state 変更の ad-hoc RPC にする**

問題: durable truth が message side effects に散らばると late join / reconnect / snapshot が壊れる。
改善: persistent facts は schema に置き、messages は player intent や transient command に使う。

**one room を backend 全体にする**

問題: lobby、matchmaking、chat、combat を1 room に詰めると ownership と scale boundary が曖昧になる。
改善: responsibility ごとに room / service boundary を分ける。

**room state を engine objects に直結**

問題: Phaser sprites / Three meshes を network code に置くと renderer と server authority が coupling する。
改善: room state は plain schema、client は renderer adapter で scene objects に map する。

**reconnect を後回しにする**

問題: disconnect は現実に起きるため、後付けだと authority、timeouts、seat ownership が複雑になる。
改善: `onDrop` / `allowReconnection` / `onReconnect` を最初から設計する。

**Colyseus server を Vercel Functions に置く**

問題: stateful websocket game server は serverless request lifecycle と相性が悪い。
改善: always-on Node host を使う。

**single-player scene logic に multiplayer を直接 retrofit**

問題: local game loop と server authority が衝突し、prediction / reconciliation の境界が曖昧になる。
改善: dedicated multiplayer scene / adapter を作る。

**dashboard env が runtime に見えていると仮定**

問題: deploy dashboard の env 設定が process に渡っていないことがある。
改善: `/health` と logs で runtime env を確認する。

**local working copy が Cloud deploy されると仮定**

問題: local changes は commit / push / deploy されなければ cloud runtime に反映されない。
改善: commit、push、deploy、verify の順で確認する。

**real level/asset contract と離れた simplified collision rectangles**

問題: simplified rectangles は実際の tilemap、sprite bounds、collision bodies とずれ、gameplay bugs を隠す。
改善: real level / asset manifest に基づく collision contract を使う。

**waiting room を完全 inert にする**

問題: strict lockout は待機 UX を悪くし、input / sync の smoke test 機会も減らす。
改善: movement / warmup attacks は許容し、damage だけ `playing` まで gate するなど product rule を決める。

**match 終了時に tick ごとに replay checkpoint を書く**

問題: 結果処理ループの中で finalization path を毎 tick 強制すると、persistence を圧迫し本当の bug を覆い隠す。
改善: match-finalization の中で最終 checkpoint を一度だけ強制し、明示的に guard する。

**inactive tab 中の cosmetic events を後で replay**

問題: tab 復帰時に古い particles / sounds / screen flashes がまとめて再生される。
改善: cosmetic events は stale window を超えたら drop し、durable state だけ resync する。

**NEVER**: renderer の都合で trust boundary を決めさせない。
**DO NOT**: room を一つの engine の scene graph 中心に設計しない。
**DON'T**: "ローカルで動いた" を reconnect / auth / deployment が正しい証拠とみなさない。

## Variation Guidance

- room topology: duel、co-op、party lobby、social hub、shard
- sync strategy: server authority、buffered interpolation、prediction + reconciliation
- message shapes: action games は directional input streams、tactics は commands、social は coarse actions
- renderer adapters: Phaser registries、Three object maps、React state bridges、ECS
- deployment: prototype は one process、production は multi-process + shared presence、multi-region は必要時のみ
- waiting UX: strict lockout、warmup movement/combat、social/lobby behavior
- analytics depth: early ops は summaries、product need がある場合だけ replay-grade capture

favorite boilerplate に収束しない。fairness、scale、simulation complexity、correction cost で architecture を選ぶ。

## 覚えておくこと

Colyseus は multiplayer truth を clean に所有し、renderer を replaceable に保つと強い。rooms は frontend scenes ではなく rules と player flows で設計する。state は canonical、messages は intentional、engine code は edge に置く。platform が曖昧なら推測せず、health field、startup log、first-write log で runtime を証明する。

Codex は境界が明確であれば並外れた Colyseus 開発ができる。よりクリーンな room model を引き出し、renderer の差し替えを可能にし、創造的な networking のトレードオフを実現し、複数の frontend にまたがって複数の architecture を探索できる。これらの指針は道を照らすものであり、道を塞ぐものではない。
