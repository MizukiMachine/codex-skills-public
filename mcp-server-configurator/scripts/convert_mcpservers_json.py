#!/usr/bin/env python3
"""
Convert a common "mcpServers" JSON snippet (Cursor/Claude Desktop style) into a
Codex `mcp_servers` TOML snippet.

Usage:
  python convert_mcpservers_json.py --json-file snippet.json
  cat snippet.json | python convert_mcpservers_json.py

If the input is a full config like:
  { "mcpServers": { "exa": { "url": "...", "headers": {...} } } }
the converter will emit `[mcp_servers.exa] ...`.

If the input is just a single server object, pass `--name`:
  cat server.json | python convert_mcpservers_json.py --name exa
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


BARE_TOML_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
ENV_VAR_RE = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")
BEARER_ENV_RE = re.compile(r"^Bearer\s+\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def toml_table_key(key: str) -> str:
    if BARE_TOML_KEY_RE.fullmatch(key):
        return key
    return toml_string(key)


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(toml_string(v) for v in values) + "]"


def toml_inline_table(values: dict[str, str]) -> str:
    parts = [f"{toml_string(k)} = {toml_string(v)}" for k, v in sorted(values.items())]
    return "{ " + ", ".join(parts) + " }"


def parse_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


@dataclass(frozen=True)
class CodexServerConfig:
    name: str
    transport: str  # "stdio" | "http"
    command: str | None = None
    args: list[str] | None = None
    cwd: str | None = None
    url: str | None = None

    env: dict[str, str] | None = None
    env_vars: list[str] | None = None

    bearer_token_env_var: str | None = None
    http_headers: dict[str, str] | None = None
    env_http_headers: dict[str, str] | None = None

    enabled: bool | None = None
    startup_timeout_sec: int | None = None
    tool_timeout_sec: int | None = None
    enabled_tools: list[str] | None = None
    disabled_tools: list[str] | None = None


def normalize_optional_keys(raw: dict[str, Any]) -> dict[str, Any]:
    # Support common camelCase variants found in other clients.
    mapped: dict[str, Any] = dict(raw)

    if "bearerTokenEnvVar" in raw and "bearer_token_env_var" not in raw:
        mapped["bearer_token_env_var"] = raw["bearerTokenEnvVar"]
    if "startupTimeoutSec" in raw and "startup_timeout_sec" not in raw:
        mapped["startup_timeout_sec"] = raw["startupTimeoutSec"]
    if "toolTimeoutSec" in raw and "tool_timeout_sec" not in raw:
        mapped["tool_timeout_sec"] = raw["toolTimeoutSec"]
    if "enabledTools" in raw and "enabled_tools" not in raw:
        mapped["enabled_tools"] = raw["enabledTools"]
    if "disabledTools" in raw and "disabled_tools" not in raw:
        mapped["disabled_tools"] = raw["disabledTools"]

    return mapped


def infer_transport(server: dict[str, Any]) -> str:
    transport_hint = server.get("type") or server.get("transport")
    if isinstance(transport_hint, str):
        hint = transport_hint.strip().lower().replace("_", "-")
        if hint in {"http", "streamable-http", "streamable"}:
            return "http"
        if hint in {"stdio"}:
            return "stdio"

    has_url = isinstance(server.get("url"), str) and bool(server.get("url").strip())
    has_command = isinstance(server.get("command"), str) and bool(server.get("command").strip())

    if has_url and not has_command:
        return "http"
    if has_command and not has_url:
        return "stdio"
    if has_url and has_command:
        raise ValueError("Ambiguous server config: contains both 'url' and 'command' (specify which to use).")
    raise ValueError("Unrecognized server config: expected 'url' (http) or 'command' (stdio).")


def split_headers(headers: dict[str, Any]) -> tuple[str | None, dict[str, str], dict[str, str]]:
    bearer_env: str | None = None
    http_headers: dict[str, str] = {}
    env_http_headers: dict[str, str] = {}

    for header_name, raw_value in headers.items():
        if not isinstance(header_name, str):
            continue
        if not isinstance(raw_value, str):
            continue

        value = raw_value.strip()
        header_lower = header_name.strip().lower()

        if header_lower == "authorization":
            m = BEARER_ENV_RE.fullmatch(value)
            if m and bearer_env is None:
                bearer_env = m.group(1)
                continue

        env_match = ENV_VAR_RE.fullmatch(value)
        if env_match:
            env_http_headers[header_name] = env_match.group(1)
        else:
            http_headers[header_name] = raw_value

    return bearer_env, http_headers, env_http_headers


def to_codex_server(name: str, raw_server: dict[str, Any]) -> CodexServerConfig:
    server = normalize_optional_keys(raw_server)
    transport = infer_transport(server)

    enabled = server.get("enabled")
    if not isinstance(enabled, bool):
        enabled = None

    startup_timeout_sec = parse_int(server.get("startup_timeout_sec"))
    tool_timeout_sec = parse_int(server.get("tool_timeout_sec"))

    enabled_tools = server.get("enabled_tools")
    if not (isinstance(enabled_tools, list) and all(isinstance(x, str) for x in enabled_tools)):
        enabled_tools = None

    disabled_tools = server.get("disabled_tools")
    if not (isinstance(disabled_tools, list) and all(isinstance(x, str) for x in disabled_tools)):
        disabled_tools = None

    if transport == "http":
        url = server.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("HTTP server is missing non-empty 'url'.")

        bearer_token_env_var = server.get("bearer_token_env_var")
        if not isinstance(bearer_token_env_var, str) or not bearer_token_env_var.strip():
            bearer_token_env_var = None

        http_headers: dict[str, str] = {}
        env_http_headers: dict[str, str] = {}

        if isinstance(server.get("http_headers"), dict):
            for k, v in server["http_headers"].items():
                if isinstance(k, str) and isinstance(v, str):
                    http_headers[k] = v

        if isinstance(server.get("env_http_headers"), dict):
            for k, v in server["env_http_headers"].items():
                if isinstance(k, str) and isinstance(v, str):
                    env_http_headers[k] = v

        if isinstance(server.get("headers"), dict):
            detected_bearer_env, detected_http, detected_env_http = split_headers(server["headers"])
            if bearer_token_env_var is None:
                bearer_token_env_var = detected_bearer_env
            http_headers.update(detected_http)
            env_http_headers.update(detected_env_http)

        return CodexServerConfig(
            name=name,
            transport="http",
            url=url,
            bearer_token_env_var=bearer_token_env_var,
            http_headers=http_headers or None,
            env_http_headers=env_http_headers or None,
            enabled=enabled,
            startup_timeout_sec=startup_timeout_sec,
            tool_timeout_sec=tool_timeout_sec,
            enabled_tools=enabled_tools,
            disabled_tools=disabled_tools,
        )

    command = server.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("STDIO server is missing non-empty 'command'.")

    args = server.get("args")
    if not (isinstance(args, list) and all(isinstance(x, str) for x in args)):
        args = None

    cwd = server.get("cwd")
    if not isinstance(cwd, str) or not cwd.strip():
        cwd = None

    env = server.get("env")
    if not (isinstance(env, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in env.items())):
        env = None

    env_vars = server.get("env_vars")
    if not (isinstance(env_vars, list) and all(isinstance(x, str) for x in env_vars)):
        env_vars = None

    return CodexServerConfig(
        name=name,
        transport="stdio",
        command=command,
        args=args,
        cwd=cwd,
        env=env,
        env_vars=env_vars,
        enabled=enabled,
        startup_timeout_sec=startup_timeout_sec,
        tool_timeout_sec=tool_timeout_sec,
        enabled_tools=enabled_tools,
        disabled_tools=disabled_tools,
    )


def render_server_toml(server: CodexServerConfig) -> str:
    lines: list[str] = []
    lines.append(f"[mcp_servers.{toml_table_key(server.name)}]")

    if server.transport == "http":
        lines.append(f"url = {toml_string(server.url or '')}")
        if server.bearer_token_env_var:
            lines.append(f"bearer_token_env_var = {toml_string(server.bearer_token_env_var)}")
        if server.http_headers:
            lines.append(f"http_headers = {toml_inline_table(server.http_headers)}")
        if server.env_http_headers:
            parts = [f"{toml_string(k)} = {toml_string(v)}" for k, v in sorted(server.env_http_headers.items())]
            lines.append("env_http_headers = { " + ", ".join(parts) + " }")
    else:
        lines.append(f"command = {toml_string(server.command or '')}")
        if server.args:
            lines.append(f"args = {toml_array(server.args)}")
        if server.env:
            lines.append(f"env = {toml_inline_table(server.env)}")
        if server.env_vars:
            lines.append(f"env_vars = {toml_array(server.env_vars)}")
        if server.cwd:
            lines.append(f"cwd = {toml_string(server.cwd)}")

    if server.startup_timeout_sec is not None:
        lines.append(f"startup_timeout_sec = {server.startup_timeout_sec}")
    if server.tool_timeout_sec is not None:
        lines.append(f"tool_timeout_sec = {server.tool_timeout_sec}")
    if server.enabled is not None:
        lines.append(f"enabled = {'true' if server.enabled else 'false'}")
    if server.enabled_tools:
        lines.append(f"enabled_tools = {toml_array(server.enabled_tools)}")
    if server.disabled_tools:
        lines.append(f"disabled_tools = {toml_array(server.disabled_tools)}")

    return "\n".join(lines)


def load_json(path: Path | None) -> Any:
    if path is None:
        return json.load(sys.stdin)
    return json.loads(path.read_text(encoding="utf-8"))


def iter_servers(data: Any, name_for_single: str | None, select_server: str | None, print_all: bool) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(data, dict) and ("mcpServers" in data or "mcp_servers" in data):
        servers = data.get("mcpServers") or data.get("mcp_servers")
        if not isinstance(servers, dict):
            raise ValueError("'mcpServers' must be an object mapping server names to configs.")

        if print_all:
            for k, v in servers.items():
                if isinstance(k, str) and isinstance(v, dict):
                    yield k, v
            return

        if select_server:
            if select_server not in servers:
                available = ", ".join(sorted(k for k in servers.keys() if isinstance(k, str)))
                raise ValueError(f"Server '{select_server}' not found. Available: {available}")
            v = servers[select_server]
            if not isinstance(v, dict):
                raise ValueError(f"Server '{select_server}' must be an object.")
            yield select_server, v
            return

        server_keys = [k for k in servers.keys() if isinstance(k, str)]
        if len(server_keys) == 1:
            only = server_keys[0]
            v = servers[only]
            if not isinstance(v, dict):
                raise ValueError(f"Server '{only}' must be an object.")
            yield only, v
            return

        available = ", ".join(sorted(server_keys))
        raise ValueError(f"Multiple servers present; pass --server <name>. Available: {available}")

    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object.")
    if not name_for_single:
        raise ValueError("Input looks like a single server object; pass --name <server-name>.")
    yield name_for_single, data


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert mcpServers JSON to Codex mcp_servers TOML.")
    parser.add_argument("--json-file", type=Path, help="Path to a JSON file. If omitted, reads stdin.")
    parser.add_argument("--name", help="Server name when input is a single server object (no mcpServers wrapper).")
    parser.add_argument("--server", help="Select one server from a multi-server mcpServers map.")
    parser.add_argument("--all", action="store_true", help="Convert all servers in the mcpServers map.")
    args = parser.parse_args()

    try:
        data = load_json(args.json_file)
        rendered: list[str] = []
        for name, raw in iter_servers(data, args.name, args.server, args.all):
            server = to_codex_server(name, raw)
            rendered.append(render_server_toml(server))
        sys.stdout.write("\n\n".join(rendered) + ("\n" if rendered else ""))
        return 0
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

