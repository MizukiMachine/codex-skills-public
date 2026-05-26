---
name: mcp-server-configurator
description: "Turn an MCP server's docs/URL into a correct Codex `mcp_servers` entry (stdio or http), with safe auth + verification steps."
metadata:
  short-description: "Configure MCP servers for Codex."
---

# MCP Server Configurator

Configure Codex MCP servers reliably, even when upstream docs are written for other clients (Cursor/Claude Desktop) or only provide a website URL.

## Philosophy: Reduce MCP Setup to 3 Decisions

Most MCP “setup pain” comes from mixing formats and guessing. Don’t guess—map.

**Before adding a server, ask:**
1. **Transport**: Is this a local launcher (**STDIO**) or a remote endpoint (**Streamable HTTP**)?
2. **Auth**: Is it OAuth, bearer token, API key header, or none?
3. **Scope**: Which tools should Codex expose (least privilege)?

**Core principles**
1. **Treat MCP config as access control**: a server can execute code (stdio) or access remote resources (http).
2. **Keep secrets out of files**: prefer environment variables (`bearer_token_env_var`, `env_http_headers`, `env_vars`).
3. **Verify after wiring**: always confirm with `codex mcp list/get` before assuming it works.

## Workflow: Docs/Website → Working `mcp_servers` Entry

### Step 0 — Intake (minimum questions)
- What’s the MCP server docs URL (or paste the install/config snippet)?
- What should we call it in Codex (e.g. `exa`, `supabase`, `ref-tools`)?
- Do you want **stdio** (local) or **http** (remote)? If unsure: share the snippet and we infer.

If the website is JS-heavy and `curl` shows no config, ask the user to copy/paste the relevant “MCP config” block.

### Step 1 — Identify transport

Use these signals from the docs:
- **STDIO**: shows `command` + `args`, mentions “stdio”, “run this locally”, `npx`, `uvx`, `docker run`, or a CLI binary.
- **Streamable HTTP**: shows a URL like `https://.../mcp`, mentions “http”, “remote”, “hosted”, or OAuth login.

### Step 2 — Map auth to Codex fields

**For Streamable HTTP** (`url = "https://.../mcp"`):
- OAuth-supported: configure `url`, then run `codex mcp login <server-name>`.
- Bearer token: set `bearer_token_env_var = "ENV_VAR_WITH_TOKEN"`.
- Custom headers:
  - Non-secret values: `http_headers = { "Header-Name" = "value" }`
  - Secret values: `env_http_headers = { "Header-Name" = "ENV_VAR" }`

**For STDIO** (`command = "..."`):
- Prefer `env_vars = ["VAR1", "VAR2"]` (and set those vars in your shell/launcher).
- Use `env = { ... }` only for non-secret or explicitly user-approved hardcoding.

### Step 3 — Produce a paste-ready `config.toml` snippet

Codex reads config from `$CODEX_HOME/config.toml` (defaults to `~/.codex/config.toml`). The top-level table must be `mcp_servers`.

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

Optional per-server knobs (place them inside the same table):
`startup_timeout_sec`, `tool_timeout_sec`, `enabled`, `enabled_tools`, `disabled_tools`.

### Step 4 — Verify in Codex

Run:
```sh
codex mcp list
codex mcp get <name>
```
If the server is Streamable HTTP and supports OAuth:
```sh
codex mcp login <name>
```

## Translation Cheat-Sheet (Other Clients → Codex)

Many docs provide a JSON snippet like:
```json
{ "mcpServers": { "supabase": { "type": "http", "url": "...", "headers": { "Authorization": "Bearer ${TOKEN}" } } } }
```

Convert it by mapping:
- `mcpServers.<name>.command` → `[mcp_servers.<name>].command`
- `mcpServers.<name>.args` → `args = [...]`
- `mcpServers.<name>.url` → `url = "..."` (Streamable HTTP)
- `headers.Authorization = "Bearer ${TOKEN}"` → `bearer_token_env_var = "TOKEN"`
- `headers.<H> = "${ENV}"` → `env_http_headers = { "<H>" = "ENV" }`

If you have a JSON snippet, you can also use the bundled converter script:
```sh
python <skill-dir>/scripts/convert_mcpservers_json.py --json-file /path/to/snippet.json
```

## Anti-Patterns to Avoid

❌ **Copying JSON config into TOML**: Codex uses `[mcp_servers.*]`, not `mcpServers`.

❌ **Hardcoding secrets**: avoid putting API keys/tokens directly in `config.toml`.

❌ **Over-exposing tools**: don’t leave everything enabled by default for high-risk servers; use `enabled_tools` / `disabled_tools`.

❌ **Skipping verification**: always run `codex mcp list/get` after edits.

## Variation Guidance (Don’t Converge)

Your output should vary based on what the docs provide:
- If docs provide a launcher command (npx/uvx/docker), produce a **stdio** table.
- If docs provide an endpoint URL, produce a **streamable http** table.
- If docs provide a JSON snippet, either **translate manually** (with notes) or **use the converter script**.
- When risk is higher, propose an `enabled_tools` allow-list and tighter timeouts.

## References

- Codex MCP config quick reference: `references/codex-mcp-servers.md`
- “Docs URL → config” extraction playbook: `references/doc-to-codex-playbook.md`
