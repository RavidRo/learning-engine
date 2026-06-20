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

## Backend authentication

The backend verifies Clerk session tokens for MCP. Configure the backend with
the same Clerk issuer/JWKS settings used by the HTTP API:

- `CLERK_ISSUER`
- `CLERK_JWKS_URL`, only when the default `<CLERK_ISSUER>/.well-known/jwks.json`
  URL is not correct
- `CLERK_AUTHORIZED_PARTIES`, required allowed frontend origins for Clerk `azp`
  claim enforcement

If Clerk is not configured, `/mcp` returns a service-unavailable response before
tool handling begins.

For Render, also set `MCP_ALLOWED_HOSTS` to the public backend host:

```text
learning-engine-backend.onrender.com
```

If Codex reports `Unexpected content type` with an `Invalid Host header` body
while connecting to production, the backend is rejecting the HTTP `Host` header
before the MCP handshake. Confirm `MCP_ALLOWED_HOSTS` includes the hostname from
the MCP URL, then redeploy or restart the backend service.

For local Docker Compose, provide the Clerk settings to the backend container.
One convenient local-only approach is to create an untracked override file:

```yaml
# compose.local.yaml
services:
  backend:
    environment:
      CLERK_ISSUER: "https://<your-clerk-domain>"
      CLERK_AUTHORIZED_PARTIES: "http://127.0.0.1:5173"
```

Then start the stack with both compose files:

```bash
docker compose -f compose.yaml -f compose.local.yaml up -d --build
```

Codex is a non-browser MCP client, so `MCP_ALLOWED_ORIGINS` is not required for
Codex. Only set `MCP_ALLOWED_ORIGINS` when a browser-based MCP client will call
the endpoint with an `Origin` header.

## Codex configuration

In the webapp, sign in and open the account menu. The account settings include
an **MCP token** page that copies the current Clerk session token and shows the
Codex setup command pattern.

Store that token for the user whose interests Codex should manage in your shell
environment before starting Codex:

```bash
export LEARNING_ENGINE_CLERK_SESSION_TOKEN="<clerk-session-token>"
```

Add the MCP server with the Codex CLI:

```bash
codex mcp add learning-engine \
  --url http://127.0.0.1:8765/mcp \
  --bearer-token-env-var LEARNING_ENGINE_CLERK_SESSION_TOKEN
```

For a deployed backend, replace the URL:

```bash
codex mcp add learning-engine \
  --url https://learning-engine-backend.onrender.com/mcp \
  --bearer-token-env-var LEARNING_ENGINE_CLERK_SESSION_TOKEN
```

Equivalent `config.toml` entry:

```toml
[mcp_servers.learning-engine]
url = "http://127.0.0.1:8765/mcp"
bearer_token_env_var = "LEARNING_ENGINE_CLERK_SESSION_TOKEN"
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
- Clerk issuer/JWKS settings are configured for the backend;
- `LEARNING_ENGINE_CLERK_SESSION_TOKEN` is set in the environment that starts Codex;
- the Clerk session token is current and belongs to the intended user;
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
