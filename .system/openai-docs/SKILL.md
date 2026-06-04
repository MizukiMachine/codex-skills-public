---
name: "openai-docs"
description: "OpenAI製品/API/Codexに関する最新の公式ドキュメントを確認する。モデル選定、アップグレード、プロンプト改善、引用付き回答、OpenAI docs MCP利用で使う。"
---

# OpenAI Docs

OpenAI developer docs から、権威があり最新の guidance を提供する。ここでの "Docs MCP" は `mcp__openaiDeveloperDocs__search_openai_docs` と `mcp__openaiDeveloperDocs__fetch_openai_doc` を指す。API reference、schema、parameter、required field に関する質問では、利用可能なら `mcp__openaiDeveloperDocs__get_openapi_spec` も使う。official-domain web search は、これらの tool が利用できない、または役に立たない場合の fallback とする。広い Codex 質問では Docs MCP より前に manual helper を使う。このスキルは model selection、API model migration、prompt-upgrade guidance も担当する。

## API Key Setup

API-backed app、script、CLI、generator、tool を build、run、configure、debug、implement する依頼では、利用可能なら最初に `openai-platform-api-key` を使う。その credential gate が解決した後、必要に応じてこのスキルに戻って最新 docs を確認する。

docs-only の質問、citation、model/API guidance、概念説明、API-backed artifact を build/run しない example では、このスキルを直接使う。

## Workflow Configuration

### Source Priority

- Codex self-knowledge では下の Codex source route を使う。この route が manual helper、Docs MCP、bounded uncertainty のどれを使うかを決める。
- Codex 以外の OpenAI docs 質問では `mcp__openaiDeveloperDocs__search_openai_docs` で最も関連する doc page を探す。
- Codex 以外の OpenAI docs 質問では、回答前に関連 page を `mcp__openaiDeveloperDocs__fetch_openai_doc` で fetch する。検索結果が noisy な場合はより narrow な Docs MCP search を実行する。official OpenAI docs URL が分かる、または見つかった場合は、web-search content に頼る前に Docs MCP でその URL を fetch してみる。
- API reference、schema、parameter、required field の質問では、関連 guide/reference page と合わせて `mcp__openaiDeveloperDocs__get_openapi_spec` で API shape を確認する。
- `mcp__openaiDeveloperDocs__list_openai_docs` は、明確な query がなく non-Codex page を browse/discover する必要がある場合だけ使う。
- model selection、"latest model"、default model の質問では、まず `https://developers.openai.com/api/docs/guides/latest-model.md` を fetch する。利用できない場合は `references/latest-model.md` を読む。
- model upgrade や prompt upgrade では、target が latest/current/default または未指定のときだけ `node scripts/resolve-latest-model-info.js` を実行する。明示 target がある場合はそれを保持する。
- ユーザーが `GPT-5.4` のような target model を明示した場合、`latest-model.md` がより新しい model を示していても要求 target を保つ。新しい guidance は optional としてだけ触れる。
- current remote guidance が必要な場合は、返された migration guide URL と prompting guide URL の両方を直接 fetch する。直接 fetch が失敗した場合は MCP/search fallback を使う。それも失敗したら bundled fallback references を使い、fallback したことを明示する。

## OpenAI Product Snapshots

1. Apps SDK: web component UI と、ChatGPT に app tools を公開する MCP server によって ChatGPT apps を構築する。
2. Responses API: agentic workflow 向けの stateful、multimodal、tool-using interaction を扱う unified endpoint。
3. Chat Completions API: conversation を構成する messages list から model response を生成する。
4. Codex: code を書き、理解し、review し、debug できる OpenAI の coding agent。
5. gpt-oss: Apache 2.0 license で公開された open-weight OpenAI reasoning models (`gpt-oss-120b` と `gpt-oss-20b`)。
6. Realtime API: natural speech-to-speech conversation など低 latency の multimodal experience を構築する。
7. Agents SDK: tool と context の利用、他 agent への handoff、partial result streaming、full trace を備えた agentic apps を構築する toolkit。

## Codex Self-Knowledge

Codex 自体に関する質問ではこの route を使う。対象は configuring、extending、operating、troubleshooting、local state、product surface、Codex behavior をどこに置くべきか、などである。codebase が plugin、skill、hook、MCP server、browser、automation に言及しているだけでは十分ではない。通常の software task ではその task に直接答える。Codex self-knowledge が適用されるかを聞かれた場合は、その meta question に短く答えてから依頼された artifact を続ける。

### Source Route

Codex manual は広い Codex synthesis の第一 source である。manual と Docs MCP は別 lane として扱い、互換の official-doc source とみなさない。公開ユーザー向け Codex product answer での source route は、manual、route が要求する場合の Docs MCP、official OpenAI web fallback、current session に surfaced している callable capability で完結する。developers.openai.com 以外の knowledge base は、この route では public product answer の source にしない。

広い Codex behavior、setup、customization、skills、plugins、MCP、hooks、`AGENTS.md`、automations、surface、local state、system-map の質問では次を行う。

1. 同一 thread で新しい manual と outline path がまだ有効なら再利用する。
2. そうでなければ、通常の writable session では skill-local helper を最初に実行する。session が明示的に read-only、shell execution が使えない、または visible policy 上 temp cache が許可されていない場合だけ、実行せずに skip する。
3. helper は既定で `$TMPDIR/openai-docs-cache`、`%TEMP%\openai-docs-cache`、`%TMP%\openai-docs-cache`、`/private/tmp/openai-docs-cache`、`/tmp/openai-docs-cache` の順に最初に使える temp cache dir を選ぶ。workspace-only write access はこの temp cache には不十分。
4. cache dir override が不要なら helper を直接実行する。helper は native `fetch` が使えない場合や proxy env vars がある場合に `curl` へ fallback するため、shell-specific proxy prefix は不要。`<skill-dir>` はこのスキルの実 path に解決する。local eval workdir では通常 `.codex/skills/openai-docs` である。

```bash
node <skill-dir>/scripts/fetch-codex-manual.mjs
```

cache dir を override する場合は `--cache-dir <cache-dir>` を渡す。Windows では helper が `%TEMP%` と `%TMP%` を自動確認する。PowerShell では `$env:TEMP\\openai-docs-cache` が典型的な明示 override である。

helper availability は、明示 read-only/no-shell policy または実際の command result で判断する。推測した sandbox や推測した helper failure だけで Docs MCP や web lookup へ切り替えない。実際に helper command が失敗した後は、下の最も narrow な official next source へ進む。

helper は freshness を検証し、`codex-manual.md` と `codex-manual.outline.md` を出力する。outline は source page と heading を line range に対応づける。Codex product fact を調べるときは outline で該当 manual section を選び、targeted に read/search する。helper が成功した後は、返された manual と outline path を Codex product fact と term coverage check の search scope として使う。

同一 thread の follow-up Codex question では、同じ manual と outline path を再利用する。manual が約1日以上古い、path が使えない、別 thread 由来または provenance が不確か、likely-current information が不足して staleness が plausible な場合は、先に refresh する。

manual が今信頼できるほど current かを聞かれた場合は、temp caching が許可されているなら helper を実行し、返された status、manual path、outline path に基づいて答える。

manual が Codex claim を解決した場合、その claim は manual から答えて source expansion を止める。docs lookup が広い user task の一部である場合は、task を続行する。manual source page と known anchor は manual-covered material の citation support として十分である。

helper が read-only、no shell、または allowed temp cache 不足により skip された場合、次の source は Docs MCP である。`mcp__openaiDeveloperDocs__search_openai_docs` を呼び、関連 hit を `mcp__openaiDeveloperDocs__fetch_openai_doc` で fetch してから web fallback に進む。

新しい manual がユーザーの Codex term や mode を使っていない場合は、manual 内で明らかに近い概念を search する。その上で exact term が documented されていないことを伝え、最も近い documented terminology を使う。prompt がその term と Codex behavior の対応を求めているなら、manual の近接 section から mapping を解決する。exact term がなお material または likely current なら、bounded uncertainty の前に narrow な Docs MCP search/fetch を1回行う。そうでなければ、その terminology/mapping claim の source lookup は完了とする。

narrowest official next source は、manual が unavailable、helper が failed、temp caching が not allowed、別の material claim が missing/likely stale、またはユーザーが page-specific citation を明示的に必要とする場合だけ使う。特定 Docs MCP search を1回行い、明確に関連する page があれば1回 fetch する。未解決の Codex capability names、acronyms、scheduling terms、exact error text では、この Docs MCP step が web search より前の next source である。manual と許可された Docs MCP gap-fill 後に残る gap は bounded uncertainty として扱う。official-domain web fallback は Docs MCP path が unavailable または unhelpful の場合だけ使う。claim がまだ確立できない場合は bounded uncertainty で止める。official docs/manual と current session で surfaced している callable capability が矛盾する場合は、矛盾を述べ、その environment では verified current-session behavior を優先する。

undocumented または private-looking な model slug、product mode label、entitlement label、account access path、rollout name では、current public docs と bounded uncertainty から答える。これらの label は public source route を外れる理由にならない。

support-style diagnostic では provider-specific web lookup より manual に基づく layer-by-layer answer を優先する。installed/enabled plugin、bundled app または connector authorization、MCP setup、workspace/admin policy、restart/new-thread expectation、最後に support/feedback の順で整理する。

source route が claim を確立しない場合は、調査範囲を広げず bounded uncertainty を返すか、support、admin、product feedback に案内する。

未解決の product terminology では、manual と許可された official next source から答える。それらの source で term が確立できない場合は、その source に基づく bounded uncertainty として答える。

### Surface Map

Codex の名詞や durable-instruction surface が重なる場合は、scope に合う最小 surface を勧める。

- Prompt / thread context: one-off task constraints。
- `AGENTS.md`: repo に永続する convention、command、verification step、review expectation。より近い nested file がその subtree で適用される。
- Project `.codex/config.toml`: trusted-repo Codex settings。sandbox、MCP、hooks、model、reasoning defaults など。
- Global config / global guidance: repo をまたぐ個人 default。
- Skill: references や scripts を伴う reusable task workflow。
- Plugin: skills、commands、tools、MCP config、hooks、assets、apps、marketplace metadata を含む installable bundle。
- MCP server / app connector: live external data/action、authorized private app/workspace data。private Google Docs、Calendar、Slack、GitHub、Notion などには web search や model memory ではなく connector を使う。
- Automation: scheduled checks、reminders、monitors、follow-up work。既存 thread の continuity が重要なら thread heartbeat を使う。
- Hook: tool call、command、file edit など lifecycle 周辺の mechanical enforcement。

mixed-scope request は1つの答えに押し込めず split する。例: "always do X, but only for this PR" は現在 run では prompt/thread context が既定で、永続化が必要な場合だけ `AGENTS.md` や project config を使う。mechanical enforcement は hooks、scheduled/follow-up work は automations にする。

必要なときはこの product map を使う。CLI は terminal-first local repo work。IDE extension は editor-attached coding。Codex app は desktop planning、review、interactive work。cloud/web は hosted parallel/offloaded work。Browser Use / in-app browser は Codex-controlled web testing。Chrome extension は user の Chrome profile を使う。Computer Use は desktop apps と OS UI を操作する。`config.toml` defaults、`requirements.toml` constraints、managed/admin policy は分けて考える。

### Boundaries and Output

- API key auth は ChatGPT、cloud task、connector access を意味しない。plugin/app/auth failure では、bundle availability、plugin installed/enabled state、connector/app authorization、MCP setup、restart/refresh expectation、workspace policy、surface availability を確認してから答える。
- sandbox または network denial には、scope を絞った escalation と明確な justification が必要。destructive commands、workspace 外への write、広い access change は明示 approval が必要。
- memory は user preference や context に使えるが、明示 prompt instruction が勝ち、memory は current external fact の source ではない。
- surface-selection の肯定回答は、recommendation、why、what to avoid、manual/source evidence の形にする。
- page-specific Codex citation が必要な場合によく使う anchor: `concepts/customization#agents-guidance` (`AGENTS.md`)、`concepts/customization#skills` (skills)、`plugins/build#plugin-structure` (plugins)、`concepts/customization#mcp` (MCP)、`config-advanced#hooks` (hooks)、`app/automations#thread-automations` (thread automations)、`config-reference#configtoml` (config)。

## If MCP Server Is Missing

MCP tools が失敗する、または OpenAI docs resources がない場合:

1. install command を自分で実行する: `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp`
2. permission/sandboxing で失敗した場合は、approval 用に1文の justification を添えて同じ command を escalated permissions で再試行する。
3. escalated attempt も失敗した場合だけ、ユーザーに install command を実行してもらう。
4. ユーザーに Codex の restart を依頼する。
5. restart 後に doc search/fetch を再実行する。

## Workflow

1. request が general docs lookup、model selection、model-string upgrade、prompt-upgrade guidance、または広い API/provider migration のどれかを明確にする。
2. Codex self-knowledge request では、上の Codex self-knowledge source procedure に従う。
3. model-selection または upgrade request では、ユーザーが latest/current/default guidance を求めている場合、bundled references より current remote docs を優先する。
   - `https://developers.openai.com/api/docs/guides/latest-model.md` を fetch する。
   - latest model ID と明示的な migration/prompt-guidance links を見つける。
   - derived URL より latest-model page の explicit links を優先する。
   - explicit named-model request では requested model target を保持し、新しい remote guidance は optional としてだけ触れる。
   - dynamic latest/current/default upgrade では `node scripts/resolve-latest-model-info.js` を実行し、可能なら返された guide URLs を両方直接 fetch する。
   - direct guide fetch が失敗した場合は developer-docs MCP tools または official OpenAI-domain search で同じ guide content を探す。
   - remote docs が unavailable の場合は bundled fallback references を使い、fallback guidance を使ったと明示する。
4. model upgrade では変更を narrow に保つ。active OpenAI API model default と、直接関連する prompt だけを安全な範囲で更新する。
5. historical docs、examples、eval baselines、fixtures、provider comparisons、provider registries、pricing tables、alias defaults、low-cost fallback paths、ambiguous older model usage は、ユーザーが明示的に upgrade を求めない限り変更しない。
6. SDK、tooling、IDE、plugin、shell、auth、provider-environment migration は、ユーザーが明示しない限り model-and-prompt upgrade から外す。
7. upgrade が API-surface change、schema rewiring、tool-handler change、literal model-string replacement と prompt edit を超える implementation work を必要とする場合は、blocked または confirmation-needed として報告する。
8. general docs lookup では precise query で docs を search し、best page と必要な exact section を fetch して、簡潔な citation 付きで答える。

## Reference Map

必要なものだけ読む。

- `https://developers.openai.com/api/docs/guides/latest-model.md`: current model-selection、"best/latest/current model" 質問。
- `scripts/fetch-codex-manual.mjs`: current Codex manual fetch、verification、local temp cache、outline generation。
- `https://developers.openai.com/codex/codex-manual.md`: setup、customization、skills、plugins、MCP、hooks、`AGENTS.md`、automations、surface behavior を含む current Codex self-knowledge synthesis。通常は helper path 経由で access し、temp caching が利用可能なら targeted file read を使う。
- `references/latest-model.md`: model-selection と "best/latest/current model" 質問向け bundled fallback。
- `references/upgrade-guide.md`: model upgrade と upgrade-planning request 向け bundled fallback。
- `references/prompting-guide.md`: prompt rewrite と prompt-behavior upgrade 向け bundled fallback。

## Quality Rules

- OpenAI docs を source of truth とし、speculation を避ける。
- Codex self-knowledge では remembered behavior に頼らず source route に従う。
- migration changes は narrow かつ behavior-preserving に保つ。
- 可能なら prompt-only upgrade を優先する。
- pricing、availability、parameters、API changes、breaking changes を invent しない。
- quote は短く policy limit 内に保ち、citation 付き paraphrase を優先する。
- 複数 page が異なる場合は差分を明示し、両方を cite する。
- official docs と verified callable current-session behavior が矛盾する場合は、広い claim や edit の前に矛盾を述べる。
- docs がユーザーの必要を満たさない場合は、その旨を言い、次の手順を提案する。

## Tooling Notes

- OpenAI-related markdown docs では web search より MCP doc tools を優先する。例外は Codex self-knowledge manual flow であり、広い Codex synthesis では上の procedure に従う。
- MCP server が installed でも meaningful result を返さない場合は web search に fallback する。
- web search fallback では official OpenAI domains (`developers.openai.com`, `platform.openai.com`) に限定し、source を cite する。
