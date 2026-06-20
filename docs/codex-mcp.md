# Configure Codex MCP Access

This guide connects Codex to the Signal Garden MCP endpoint so Codex can manage
interests and sources through the project backend.

## Endpoint

The backend exposes a Streamable HTTP MCP endpoint at:

```text
http://127.0.0.1:8765/mcp
```

For a Render deployment, use the deployed backend URL instead:

```text
https://learning-engine-backend.onrender.com/mcp
```

## Backend token

The backend disables MCP until `MCP_AUTH_TOKEN` is configured. Generate a strong
token and provide it to the backend process:

```bash
openssl rand -hex 32
```

For Render, set `MCP_AUTH_TOKEN` as a secret environment variable in the Render
Dashboard for `learning-engine-backend`.

For Render, also set `MCP_ALLOWED_HOSTS` to the public backend host:

```text
learning-engine-backend.onrender.com
```

If Codex reports `Unexpected content type` with an `Invalid Host header` body
while connecting to production, the backend is rejecting the HTTP `Host` header
before the MCP handshake. Confirm `MCP_ALLOWED_HOSTS` includes the hostname from
the MCP URL, then redeploy or restart the backend service.

For local Docker Compose, pass the token to the backend container. One convenient
local-only approach is to create an untracked override file:

```yaml
# compose.local.yaml
services:
  backend:
    environment:
      MCP_AUTH_TOKEN: "<generated-token>"
```

Then start the stack with both compose files:

```bash
docker compose -f compose.yaml -f compose.local.yaml up -d --build
```

Codex is a non-browser MCP client, so `MCP_ALLOWED_ORIGINS` is not required for
Codex. Only set `MCP_ALLOWED_ORIGINS` when a browser-based MCP client will call
the endpoint with an `Origin` header.

## Codex configuration

Store the same token in your shell environment before starting Codex:

```bash
export LEARNING_ENGINE_MCP_TOKEN="<generated-token>"
```

Add the MCP server with the Codex CLI:

```bash
codex mcp add learning-engine \
  --url http://127.0.0.1:8765/mcp \
  --bearer-token-env-var LEARNING_ENGINE_MCP_TOKEN
```

For a deployed backend, replace the URL:

```bash
codex mcp add learning-engine \
  --url https://learning-engine-backend.onrender.com/mcp \
  --bearer-token-env-var LEARNING_ENGINE_MCP_TOKEN
```

Equivalent `config.toml` entry:

```toml
[mcp_servers.learning-engine]
url = "http://127.0.0.1:8765/mcp"
bearer_token_env_var = "LEARNING_ENGINE_MCP_TOKEN"
tool_timeout_sec = 60
enabled = true
```

Use `~/.codex/config.toml` for a personal global setup, or this repository's
`.codex/config.toml` for a project-scoped setup after trusting the project.
Do not commit real token values.

## Verify

Start or restart Codex after setting the environment variable, then run:

```bash
codex mcp list
```

In the Codex TUI, use:

```text
/mcp
```

The `learning-engine` server should appear as enabled. If it does not, check:

- the backend is running and `http://127.0.0.1:8765/api/health` returns `{"status":"ok"}`;
- `MCP_AUTH_TOKEN` is set for the backend;
- `LEARNING_ENGINE_MCP_TOKEN` is set in the environment that starts Codex;
- both token values match exactly;
- the MCP URL matches the backend you are using.
- for deployed backends, `MCP_ALLOWED_HOSTS` includes the hostname from the MCP
  URL.

## Available MCP scope

The v1 MCP server is intentionally limited to interest management. It lets Codex:

- list interests and sources;
- create, update, pause, resume, and soft-delete interests;
- add, update, pause, resume, and soft-delete sources.

It does not expose update collection, briefing retrieval, provider credentials,
or source image resolution.
