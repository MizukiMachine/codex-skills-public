---
name: mcp-server-configurator
description: "MCPサーバーのドキュメントやURLからCodex用のmcp_servers設定を作る。stdio/http、認証、検証手順を整理するときに使う。"
metadata:
  short-description: "Codex向けMCPサーバー設定"
---

# MCP Server Configurator

上流ドキュメントが Cursor / Claude Desktop 向けだったり、Web サイト URL しかない場合でも、Codex 向け MCP server 設定を確実に作る。

## 考え方: MCP 設定を3つの判断へ分解する

MCP の設定で詰まりやすい原因は、形式を混ぜることと推測で進めること。推測せず、対応関係へ map する。

**server を追加する前に確認すること:**

1. **Transport**: local launcher の **STDIO** か、remote endpoint の **Streamable HTTP** か
2. **Auth**: OAuth、bearer token、API key header、認証なしのどれか
3. **Scope**: Codex にどの tools を公開するか。least privilege を優先する

**基本原則**

1. **MCP config は access control として扱う**: server は stdio で code 実行、または http で remote resource access が可能
2. **secrets を file に置かない**: `bearer_token_env_var`、`env_http_headers`、`env_vars` など環境変数参照を優先する
3. **設定後に検証する**: 動くと仮定せず、必ず `codex mcp list/get` で確認する

## ワークフロー: Docs/Website から動く `mcp_servers` entry へ

### Step 0: 最小限の intake

- MCP server docs URL、または install/config snippet は何か
- Codex での名前は何にするか。例: `exa`, `supabase`, `ref-tools`
- **stdio** (local) と **http** (remote) のどちらか。不明なら snippet から推定する

Web サイトが JS-heavy で `curl` では config が取れない場合、該当の "MCP config" block をユーザーに貼ってもらう。

### Step 1: transport を特定する

docs から次の signal を見る。

- **STDIO**: `command` + `args`、"stdio"、"run this locally"、`npx`、`uvx`、`docker run`、CLI binary
- **Streamable HTTP**: `https://.../mcp` のような URL、"http"、"remote"、"hosted"、OAuth login

### Step 2: auth を Codex fields へ map する

**Streamable HTTP** (`url = "https://.../mcp"`):

- OAuth-supported: `url` を設定し、`codex mcp login <server-name>` を実行する
- Bearer token: `bearer_token_env_var = "ENV_VAR_WITH_TOKEN"` を設定する
- Custom headers:
  - secret でない値: `http_headers = { "Header-Name" = "value" }`
  - secret 値: `env_http_headers = { "Header-Name" = "ENV_VAR" }`

**STDIO** (`command = "..."`):

- `env_vars = ["VAR1", "VAR2"]` を優先し、shell/launcher 側でその変数を設定する
- `env = { ... }` は secret でない値、またはユーザーが hardcode を明示承認した場合だけ使う

### Step 3: paste-ready な `config.toml` snippet を作る

Codex は `$CODEX_HOME/config.toml` を読む。既定は `~/.codex/config.toml`。top-level table は `mcp_servers`。

**STDIO template**

```toml
[mcp_servers.<name>]
command = "npx"
args = ["-y", "<package-or-binary>", "--stdio"]
env_vars = ["SOME_API_KEY"]  # whitelist vars to pass through
```

**Streamable HTTP template**

```toml
[mcp_servers.<name>]
url = "https://example.com/mcp"
bearer_token_env_var = "SOME_TOKEN"  # optional
env_http_headers = { "x-api-key" = "SOME_API_KEY" }  # optional
```

任意の per-server knobs は同じ table 内に置く。

`startup_timeout_sec`, `tool_timeout_sec`, `enabled`, `enabled_tools`, `disabled_tools`

### Step 4: Codex で検証する

```sh
codex mcp list
codex mcp get <name>
```

Streamable HTTP で OAuth を support する場合:

```sh
codex mcp login <name>
```

## 変換チートシート: Other Clients から Codex へ

多くの docs は次のような JSON snippet を示す。

```json
{ "mcpServers": { "supabase": { "type": "http", "url": "...", "headers": { "Authorization": "Bearer ${TOKEN}" } } } }
```

対応関係:

- `mcpServers.<name>.command` -> `[mcp_servers.<name>].command`
- `mcpServers.<name>.args` -> `args = [...]`
- `mcpServers.<name>.url` -> `url = "..."` (Streamable HTTP)
- `headers.Authorization = "Bearer ${TOKEN}"` -> `bearer_token_env_var = "TOKEN"`
- `headers.<H> = "${ENV}"` -> `env_http_headers = { "<H>" = "ENV" }`

JSON snippet がある場合は同梱 converter script も使える。

```sh
python <skill-dir>/scripts/convert_mcpservers_json.py --json-file /path/to/snippet.json
```

## 避けること

- **JSON config を TOML へそのまま貼る**: Codex は `mcpServers` ではなく `[mcp_servers.*]` を使う
- **secret の hardcode**: API key/token を `config.toml` に直接置かない
- **tool の過剰公開**: high-risk server は `enabled_tools` / `disabled_tools` で絞る
- **検証を省く**: edit 後は必ず `codex mcp list/get` を実行する

## Variation Guidance

docs が提供する情報に合わせて output を変える。

- launcher command (npx/uvx/docker) があれば **stdio** table を作る
- endpoint URL があれば **streamable http** table を作る
- JSON snippet があれば、手動変換するか converter script を使う
- risk が高い場合は `enabled_tools` allow-list と短めの timeout を提案する

## 参照

- Codex MCP config quick reference: `references/codex-mcp-servers.md`
- "Docs URL -> config" extraction playbook: `references/doc-to-codex-playbook.md`
