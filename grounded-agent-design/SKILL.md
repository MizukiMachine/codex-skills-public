---
name: grounded-agent-design
description: "情報境界を持つLLMシステムを設計・レビューする。権限付きRAG、非公開状態、役割別の可視情報、fresh call / restricted sub-agent / scoped worker による生成分離、根拠確認、漏洩・幻覚対策の制御ループで使う。"
---

# Grounded Agent Design

## 目的

異なる actor が異なる情報だけを見られ、各 generation が grounded / on-task / within bounds に保たれる LLM system を作る。仕事は inseparable な2 layers。

- **Boundary (design-time)**: viewer ごとに single authoritative state を projection し、actor が許可された context だけから行動するようにする。これは prompt instruction ではなく product layer
- **Control loop (run-time)**: 各 stochastic generation を deterministic **Direct -> Censor -> Correct** loop で包み、boundary と faithfulness を enforce し、失敗時は safe output に fallback する

boundary は precondition、control loop は enforcement。boundary はその turn で何が true / visible かを決め、loop は output をその projection と照合して修正する。

適用先: permissioned RAG、enterprise search、support/legal/medical/HR bots、multi-agent RAG、AI NPC、TRPG、social-deduction / negotiation games、meeting/simulation agents、tutoring、private notes、hidden roles、document ACLs、asymmetric objectives を持つ assistant。

## Core Principle

one all-knowing LLM に全 truth を渡して "be careful" と頼まない。stochastic generator は probabilistically に leak / fabricate する。置き換える手段は2つ。

1. **information boundaries として system を model 化する**
   - who is acting、what they know、what they may reveal、what they optimize、safe output contract、required checks を分ける
   - actor context は code から allowlisted data で render し、"pretend you don't know X" に頼らない
2. **quality を prompt ではなく loop の property にする**
   - LLM を fast / fluent / unreliable generator として扱う
   - generation 前に deterministic plan を作り、output 後に ground truth と比較し、specific violated invariant を revision hint として返す
   - attempts を bound し、fallback する

**load-bearing invariant:** model は visible context にあるものだけを real として扱える。boundary layer が visible context を作り、censor が output を check する。

**generation isolation invariant:** hidden / forbidden / cross-actor private state
を見た model invocation で、actor-limited / public free text を生成しない。
orchestrator は full state を持ってよいが、speaker / answerer / downstream
agent は projection だけを受け取る fresh model call、restricted sub-agent、
または scoped worker として実行する。sub-agent を使っても、unrestricted
files / DB / RAG / memory / logs / tools を読めるなら boundary ではない。

tradeoff priority: correctness / faithfulness / no-leak > staying on-task > style/voice > latency。fluent fabrication より dull-but-true fallback、leak より redacted answer。

実装前に確認すること:

- authoritative state と各 viewer projection は何か。どの code path が何を strip するか
- actor-limited / public output はどの isolated generation boundary（fresh call、restricted sub-agent、scoped worker）で作るか。その境界で tool / retrieval / memory / filesystem access は同じ scope に絞られているか
- この turn の ground truth は何か。output が参照できる facts/transcript は何か
- hidden にすべき private state、other actors' secrets、system rules、tool traces、retrieval internals は何か
- cold context か。first turn / empty history なら committed move を強制しない
- safe fallback output は何か。常に valid、boring、leak-free

## Two Layers

```text
authoritative state (server source of truth)
  └─ per-viewer projection / redaction        ← BOUNDARY (precondition)
       └─ for each actor whose turn it is:
            definePlan(projection) → renderPlan ← DIRECT
            runRevisionLoop(generate, validate, fallback)
                 generate: isolated call / restricted sub-agent / scoped worker
                 validate: runValidators(...)    ← CENSOR
                 fallback: safe deterministic    ← CORRECT
            commit accepted output to state
            extract structured signals (round-trip) ← feeds anti-repetition
       └─ view-specific redaction before client / next agent ← BOUNDARY (egress)
```

`allowedFacts` は手書きせず projection から導く。generation loop は per generation で synchronous に保つ。actors/turns の concurrency は別 latency runtime に分ける。

## ワークフロー

**Phase A: Boundary を設計する** (`references/boundary-design.md`):

1. **actors / scopes を map**
   - users、agents、tools、documents、memories、system processes、external viewers
   - role、goal、allowed inputs、forbidden inputs、allowed outputs、downstream consumers
   - hidden roles、private memories、public history、spectator views（games）、auth、ACLs、citations、tool traces（RAG）も含める。
2. **information を sensitivity lattice で分類**
   - `public / user_provided / confidential / secret / forbidden`
   - retrieval results、summaries、memories、diagnostics も data として sensitivity を持つ
3. **prompts 前に access matrix を作る**
   - denylists より allowlists
   - role-visible context は code で render
4. **generation isolation を選ぶ**
   - public / actor-limited free text は、hidden state を見た invocation から直接生成しない
   - acceptable: projection だけを渡す fresh API call、restricted sub-agent、scoped worker
   - tool / retrieval / filesystem / memory / logs も projection と同じ scope に制限する
5. **risk に応じて output contracts を選ぶ**
   - naturalness が価値なら free text
   - actions、target selection、retrieval plans、auth decisions、safety gates は JSON/typed schema
6. **already-authorized context から prompts を作る**
   - user input、retrieved docs、emails、tickets、chat logs、DB text は instructions ではなく untrusted data
7. **egress で view-specific redaction**
   - full data は server-side に保存し、client / next agent には mask 済み snapshot

**Phase B: Control Loop を作る** (`references/plan-object.md`, `references/failure-modes.md`, `references/validators.md`):

7. **plan object (Direct) を定義**
   - per-turn contract を data として model 化
   - `intents` / `allowedFacts` は projection から導く
   - cold-context rule は `definePlan` に入れる
8. **failure modes と validators (Censor) を列挙**
   - app で実際に起きる modes だけ実装
   - cue words は hardcoded logic ではなく `Lexicon` config
   - real transcripts で calibrate
9. **revision loop (Correct) を wire**
   - bounded attempts
   - specific violated invariant を hint として返す
   - channel ごとの safe deterministic fallback
   - attempt diagnostics
10. **starter harness を adapt**
    - `assets/control-layer/` を copy し、plan derivation、lexicon、validator set を差し替える
    - loop と types は保つ
11. **verify**
    - known-bad / known-good outputs
    - hint feedback
    - fallback path
    - secret state が context builder に入っていないこと

## 参照ファイル

| Topic | File | Use When |
|-------|------|----------|
| Information-boundary design | [boundary-design.md](references/boundary-design.md) | actors/scopes、sensitivity、access matrix、redaction、prompt-injection defense |
| Plan / director layer | [plan-object.md](references/plan-object.md) | plan、intents、fact whitelist、cold-context、output channels |
| Failure taxonomy | [failure-modes.md](references/failure-modes.md) | hallucination / quality failures と revision hints |
| Validator patterns | [validators.md](references/validators.md) | detectors、patterns-as-config、metadata round-trip、anti-repetition |
| Architecture | [architecture.md](references/architecture.md) | loop の接続位置、fallback、diagnostics、latency runtime |

## Starter Harness

`assets/control-layer/` は dependency-free typed runnable reference implementation。そのままコピーして適応させる。

| File | Role |
|------|------|
| `plan.ts` | Direct: `ControlPlan`、`definePlan`、`renderPlan` |
| `validators.ts` | Censor: `Validator` 型、`groundedReferences`、`noBoundaryLeak`、`hasForwardSubstance`、`notRepetitive`、`runValidators` |
| `revisionLoop.ts` | Correct: bounded attempts、hint feedback、safe fallback、diagnostics |
| `lexicons/en.yaml`, `lexicons/ja.yaml` | detection cue words。domain/language 調整はここ |
| `loadLexicon.ts` | lexicon YAML を `Lexicon` に読み込む（dependency-free; `loadLexicon("en")` またはパス指定） |
| `lexicons.ts` | YAML から `englishLexicon` / `japaneseLexicon` を公開する薄い loader |
| `index.ts` | barrel export |
| `demo.ts` | API key 不要の self-check |

detection strategy は code、patterns は YAML。新 language は `lexicons/<lang>.yaml` を追加し `loadLexicon("<lang>")`。

verify:

```bash
node --import tsx assets/control-layer/demo.ts
```

期待値は `ALL PASS`。`tsx` が resolve できる project から実行する。なければ `npm i -D tsx`（harness 自体は dependency-free で、`tsx` は TS runner にすぎない）。

## Patterns

control loop の形:

```ts
const plan = definePlan({ hasPriorContext, intents, allowedFacts, mustNotReveal, wantsForwardMove });
const validators = [groundedReferences(lexicon), noBoundaryLeak, hasForwardSubstance(lexicon)];
const { value, accepted, usedFallback } = await runRevisionLoop({
  generate: (hint) => callIsolatedGenerator({
    context: projectedContext,
    prompt: buildPrompt(renderPlan(plan), hint),
    tools: scopedToolsForActor(actorId)
  }),
  validate: (out) => runValidators({ output: out, visibleFacts, entities, plan }, validators),
  fallback: () => safeDeterministicLine(plan),
  maxAttempts: 3,
  onAttempt: (info) => telemetry.record(info)
});
```

cold-context rule:

```ts
// first turn: history が存在しない。「commit to a position」を強制すると、model は反応する
// ための history を捏造する。代わりに open する — ただし substance は要求し続ける。
const plan = definePlan({ hasPriorContext: false, intents: [openingIntent], wantsForwardMove: true });
// plan.requiresForwardMove === false  (cold context では definePlan が override する)
```

RAG pattern:

- generation 前に ACL-filter documents
- `allowedFacts` = retrieved chunks
- answerer は ACL-filter 後の snippets だけを持つ isolated generation context で実行
- censor は chunk に trace しない claims を reject
- internal fields/scores は egress で redact

full pipeline と hard rules: `references/boundary-design.md` → RAG pattern。

simulation / game pattern:

- actor ごとに role-visible secrets を project
- public / private speech は actor projection だけを渡す fresh call / restricted sub-agent / scoped worker で生成
- public speech と action/vote を channel 分離
- spoken line は invented events / boundary leaks で censor
- decision は legal-target check

full pipeline と hard rules: `references/boundary-design.md` → Simulation / game pattern。

**Prompt boundary template:** コピーして使えるコンパクトな起点 prompt は `references/boundary-design.md` → Prompt boundary template にある。

## 避けること

**prompt-only faithfulness / "make things up しないよう指示した"**

問題: stochastic generator は probabilistically に instruction を破る。instruction は発生率を下げるだけで、下限を enforce しない。
改善: allowed facts を enumerate し、output をそれと照合する。censor が floor を enforce する。

**"pretend you don't know X" を prompt に書く**

問題: secret が context に入っているため、pressure 下で leak する。
改善: information boundary を作り、その actor の context に X を入れない。prompt text ではなく context builder を grep する。

**hidden state を見た invocation で public / actor-limited output を作る**

問題: "言わないで" と同じ failure mode になる。生成器は hidden state を内部文脈に持っている。
改善: orchestrator だけが full state を読み、projection だけを fresh call / restricted sub-agent / scoped worker に渡す。sub-agent の tools / memory / retrieval / filesystem も同じ scope に絞る。

**denylists over allowlists**

問題: hide するものの列挙は必ず漏れが出る。
改善: authorized data の allowlist から role-visible context を render する。

**retrieved/user text を instructions として扱う**

問題: documents、tickets、emails、chat logs は "ignore your rules / reveal secrets / change roles" を含み得る。
改善: evidence/content として扱い、developer instructions にはしない。

**same prompt で discard-and-retry**

問題: 同じ prompt は同じ distribution を re-roll するだけ。
改善: specific violated invariant を revision hint として返す。

**opening turn で stance 強制**

問題: real history がない状態で "take a position" を求めると、invent する以外に満たせない。
改善: cold-context plans は topic を open し、forward-move を緩めつつ passive filler は reject する。

**language patterns を validator logic に hardcode**

問題: unmaintainable かつ monolingual になる。
改善: detection strategy は code に置き、cue words は `Lexicon` に置く。

**unbounded correction**

問題: stubborn model が永久 loop する。
改善: attempts を bound し、safe deterministic fallback に落とす。

**redaction を prompt instruction にする**

問題: redaction は prompt ではなく product layer の責務。
改善: full data は server-side に保存し、view-specific snapshots を emit し、egress 前に mask する。

## Variation Guidance

- **Output channel**: public/spoken line は boundary + grounding + substance。structured decision は schema parse + legal-choice
- **Domain**: RAG は claim-to-chunk、sim は no invented events + no boundary leak、tutoring は learner を進めつつ unstated facts を assert しない
- **Language**: lexicon を swap。Japanese は word membership より phrase patterns
- **Risk level**: high-stakes では attempts と validators を厳しくし、fallback を保守的に
- **Repetition pressure**: multi-actor では `notRepetitive` を prior angles で feed

## Review Checklist

- authoritative state と viewer projection の code path は何か
- actor-limited / public generation は hidden state を見ていない fresh/scoped context で実行されるか
- sub-agent / worker を使う場合、その tools、memory、retrieval、filesystem、logs は projection と同じ scope に制限されているか
- prompts は allowlisted data から作られているか
- `allowedFacts` は projection から導かれているか
- free text / structured outputs は分離され、別々に validation されているか
- IDs、citations、claims、actions を ground truth と照合しているか
- user/retrieved text は data として扱われているか
- cold-context rule は `definePlan` にあるか
- client / downstream agent 前に何を redact しているか
- malformed/stale/leaking/low-evidence output の correction/fallback は bounded か
- diagnostics と tests があるか

## 検証

- `node --import tsx assets/control-layer/demo.ts` -> `ALL PASS`
- 各 failure mode で known-bad が violation、known-good が pass
- retry 時に revision hint が generator に届く
- all attempts fail 時に fallback が safe output を返す
- hidden state が prompt builder ではなく context construction に入っていないことを grep
- boundary tests: unauthorized document が prompt context に入らない、illegal target/document/action ID を選べない、public output が hidden state を露出しない、isolated generator / sub-agent が unrestricted tools or memory にアクセスできない、view-specific redaction が private fields を remove

## Portfolio Framing

説明例:

```text
I designed the system around information boundaries rather than a single all-knowing prompt, then wrapped each generation in a deterministic Direct->Censor->Correct control loop. Each agent receives only the context it is authorized to see, free-form language is separated from structured decisions, every user-facing view is redacted from authoritative state, and every turn is validated against enumerated ground truth with a bounded revision loop and a safe fallback. This keeps the LLM expressive while keeping permissions, hidden state, citations, grounding, and workflow actions controllable and testable.
```
