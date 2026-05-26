# Docs URL → Codex `mcp_servers` Playbook

Use this when a user gives you a website/README for an existing MCP server and asks “add this to Codex”.

## 1) Extract the config signal (fast)

When you have shell access, start with a cheap scrape:

```sh
curl -fsSL "<docs-url>" | rg -ni "mcpServers|mcp_servers|command|args|url|headers|authorization|bearer|oauth|stdio|streamable|token|api[_-]?key" | head
```

If the site is JS-rendered and the scrape yields nothing useful:
- Ask the user to **paste the MCP configuration snippet** from the docs.
- Or ask for the repo/README link that contains the raw config block.

## 2) Decide transport (don’t guess)

**STDIO** if the docs show:
- a local launcher: `npx …`, `uvx …`, `docker run …`, “run this command”
- fields like `command`/`args`, or mention “stdio”

**Streamable HTTP** if the docs show:
- an endpoint: `https://…/mcp` or `http://localhost:…/mcp`
- fields like `url`, “remote/hosted”, “OAuth login”

If docs show both, ask which the user prefers (remote managed vs local install).

## 3) Translate common doc formats

### A) “mcpServers” JSON snippets (Cursor/Claude Desktop style)

These often look like:
```json
{ "mcpServers": { "service": { "type": "http", "url": "…", "headers": { "Authorization": "Bearer ${TOKEN}" } } } }
```

Convert to Codex TOML:
- `url` → `[mcp_servers.service].url`
- `headers.Authorization = "Bearer ${TOKEN}"` → `bearer_token_env_var = "TOKEN"`
- `headers.<H> = "${ENV}"` → `env_http_headers = { "<H>" = "ENV" }`

Tip: use the bundled converter:
```sh
python <skill-dir>/scripts/convert_mcpservers_json.py --json-file snippet.json
```

### B) Plain “run this command” instructions

Docs may say:
- “Install with npm” → `command = "npx"` + `args = ["-y", "<pkg>"]`
- “Run this binary” → `command = "<binary>"` + args as documented

If they mention an API key, keep it in env and only whitelist it via `env_vars`.

## 4) Produce output that is immediately usable

Always provide:
- A paste-ready `[mcp_servers.<name>]` snippet for `~/.codex/config.toml`
- A short list of required env vars (names only, no secrets)
- Verification commands: `codex mcp list` + `codex mcp get <name>`
- If OAuth is involved: `codex mcp login <name>`

Optionally (recommended):
- A minimal `enabled_tools = [...]` allow-list when the server exposes many tools or has high blast radius.

## 5) Watch-outs (high-frequency failures)

- Users paste JSON `mcpServers` into TOML unchanged (wrong format).
- Auth headers need `Bearer ` prefix: prefer `bearer_token_env_var` over `env_http_headers` for Authorization bearer patterns.
- Some servers require query params in the URL (keep them in `url = "…?x=y"`).
- If the server is slow to start, bump `startup_timeout_sec` instead of retrying blindly.
