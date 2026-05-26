# Codex MCP Servers (Quick Reference)

This is a compact reference for configuring MCP servers in Codex.

## Where config lives

- Main config file: `$CODEX_HOME/config.toml` (defaults to `~/.codex/config.toml`).
- MCP servers are configured under the **top-level** TOML table `mcp_servers`.

## Two supported transports

### 1) STDIO (local launcher)

Use this when the server is started locally via a command (npm package, uvx tool, binary, docker wrapper).

```toml
[mcp_servers.server_name]
command = "npx"
args = ["-y", "mcp-server"]

# Optional env config:
env = { "API_KEY" = "value" }      # sets variables (avoid for secrets)
env_vars = ["API_KEY2"]            # whitelists passthrough variables
cwd = "/path/to/server"            # working directory for the command
```

Notes:
- Codex propagates a default env-var whitelist; use `env_vars` to add more passthrough variables.

### 2) Streamable HTTP (remote URL)

Use this when the docs provide an MCP endpoint URL (localhost or remote).

```toml
[mcp_servers.server_name]
url = "https://example.com/mcp"

# Auth options (pick one pattern):
bearer_token_env_var = "ENV_VAR"                   # Authorization: Bearer <env>
http_headers = { "Header-Name" = "Header-Value" }  # hard-coded headers
env_http_headers = { "Header-Name" = "ENV_VAR" }   # header value from env var
```

OAuth:
- For streamable HTTP servers that support OAuth, authenticate via:
  - `codex mcp login <server-name>`
  - `codex mcp logout <server-name>`

## Per-server knobs (optional)

Place these inside `[mcp_servers.<name>]`:

```toml
startup_timeout_sec = 20
tool_timeout_sec = 30
enabled = false
enabled_tools = ["search", "summarize"]
disabled_tools = ["search"]
```

When both allow/deny lists are set, Codex applies `enabled_tools` first, then removes `disabled_tools`.

## Useful CLI commands

```sh
codex mcp --help
codex mcp add <name> -- <launcher> <args...>
codex mcp list
codex mcp list --json
codex mcp get <name>
codex mcp get <name> --json
codex mcp remove <name>
```

Source: `https://github.com/openai/codex/blob/main/docs/config.md#mcp_servers`
