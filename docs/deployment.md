# Render Deployment

This repository uses Render as a cloud provider for deploying the app without managing a server directly. Configurations are described in a blueprint:

```text
render.yaml
```

## Target architecture

The Blueprint creates three Render resources:

1. `learning-engine-frontend` — a free static site built from `webapp/`.
2. `learning-engine-backend` — a Docker web service built from `backend/`.
3. `learning-engine-db` — a managed Render Postgres database on Render's free plan.

## Region

The backend service and Postgres database are configured for Render's
`frankfurt` region because Frankfurt is the closest available Render
service/datastore region to Israel.

## Deployment

Render is synced to the main branch, commit/merger to `main` in order to deploy changes.

## MCP interest management

The backend exposes an MCP Streamable HTTP endpoint at:

```text
https://<backend-service-host>/mcp
```

For the default Render service name, that is:

```text
https://learning-engine-backend.onrender.com/mcp
```

MCP is disabled until `MCP_AUTH_TOKEN` is configured. When the token is missing
or blank, `/mcp` returns a service-unavailable response explaining that MCP is
not configured.

Set `MCP_AUTH_TOKEN` in the Render Dashboard as a secret value. MCP clients must
send it on every request:

```text
Authorization: Bearer <MCP_AUTH_TOKEN>
```

Browser-origin MCP clients must also be allowlisted with `MCP_ALLOWED_ORIGINS`.
Set it to a comma-separated list of exact origins, such as:

```text
https://chat.openai.com, https://app.example.com
```

Origin validation only applies when a request includes an `Origin` header. If a
browser request includes `Origin` and `MCP_ALLOWED_ORIGINS` is unset or does not
contain that exact origin, the request is rejected before MCP tool handling.
Non-browser clients that omit `Origin` rely on the bearer token.

The v1 MCP surface is intentionally limited to interest management. It supports
listing interests, creating/updating/pausing/resuming/soft-deleting interests,
and adding/updating/pausing/resuming/soft-deleting sources. Update collection,
briefing retrieval, provider credentials, and source image resolution are out of
scope for this MCP endpoint.
