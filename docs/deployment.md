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

Render syncs to the main branch and deploys on every commit to `main`.

## Clerk authentication

The webapp and backend require Clerk before user-owned data can load.

Set these environment variables in the Render Dashboard:

- `VITE_CLERK_PUBLISHABLE_KEY` on `learning-engine-frontend`.
- `CLERK_ISSUER` on `learning-engine-backend`, for example `https://<your-clerk-domain>`.
- `CLERK_JWKS_URL` on `learning-engine-backend` only when the default
  `<CLERK_ISSUER>/.well-known/jwks.json` URL is not correct.
- `CLERK_AUTHORIZED_PARTIES` on `learning-engine-backend` as a comma-separated
  list of allowed frontend origins when the deployment should enforce Clerk's
  `azp` claim, for example `https://learning-engine-frontend.onrender.com`.

Do not commit Clerk secret values. The current backend verifies Clerk session
JWTs with the issuer and JWKS URL; it does not require a Clerk secret key for the
implemented request path.

### Existing data bootstrap

RAV-18 changes existing global interest and collection tables into user-owned
data. Fresh deployments need no bootstrap. For an existing deployment that
already has global rows, choose the Clerk user id that should own those rows,
record it in the deployment runbook, and run a one-time database backfill before
deploying code that enforces user predicates.

The backfill must set that Clerk user id on every existing interest, source,
source ignore keyword, collection, and saved update row before adding the new
user-owned uniqueness constraints. If no owner can be chosen, export the old
data before the deployment and re-import it after signing in as the intended
user.

## MCP interest management

The backend exposes an MCP Streamable HTTP endpoint at:

```text
https://<backend-service-host>/mcp
```

For the default Render service name, that is:

```text
https://learning-engine-backend.onrender.com/mcp
```

MCP authentication uses the same Clerk session bearer tokens as the HTTP API.
Clients must send a valid Clerk session token on every request:

```text
Authorization: Bearer <clerk-session-token>
```

If Clerk issuer or JWKS configuration is missing, `/mcp` returns a
service-unavailable response explaining that Clerk authentication is not
configured. Missing, expired, malformed, or unverifiable tokens return
unauthorized.

MCP host validation is also enabled. Set `MCP_ALLOWED_HOSTS` to the public
backend host used by MCP clients, such as:

```text
learning-engine-backend.onrender.com
```

If this value is missing in production, MCP clients can fail during startup with
an `Invalid Host header` response before MCP tool handling begins. Localhost
hostnames are allowed by default for local development.

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
