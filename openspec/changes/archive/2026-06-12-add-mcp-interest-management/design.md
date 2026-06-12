## Context

The backend is a FastAPI service with a clean application port for `InterestRepository`. The current HTTP API reads and writes the entire `InterestsPayload`, while the webapp performs client-side commands and then posts the full payload. Persistence requires stable IDs for interests and sources, and deletion is already modeled as soft deletion with `deletedAt`.

MCP introduces a new public integration surface for AI agents. That surface can mutate user configuration, so it needs explicit authentication, browser-origin protection, strict validation, and command-style semantics that do not make agents preserve the entire interest document.

## Goals / Non-Goals

**Goals:**

- Serve a remote MCP Streamable HTTP endpoint from the existing FastAPI backend process at `/mcp`.
- Require bearer-token authentication through `MCP_AUTH_TOKEN`.
- Return a clear service-unavailable response when MCP is not configured.
- Validate browser-origin requests through `MCP_ALLOWED_ORIGINS`.
- Use the official Python MCP SDK for protocol handling.
- Expose only interest/source management tools in the first version.
- Implement safe command-style operations through the existing `InterestRepository` boundary.
- Generate IDs server-side for MCP-created interests and sources.
- Preserve existing domain validation, source types, priorities, enabled flags, and soft-deletion behavior.
- Update Render configuration and deployment docs without committing secret values.

**Non-Goals:**

- Add user accounts, OAuth, per-agent scopes, or multi-tenant authorization.
- Expose update collection, briefing retrieval, source image resolution, or provider token management through MCP.
- Replace the existing `/api/interests` HTTP endpoints or migrate the webapp to command endpoints.
- Add hard-delete semantics for interests or sources.
- Add fuzzy name matching for write operations.

## Decisions

1. Host MCP in the existing FastAPI backend process.

   The backend already owns persistence, lifecycle startup, and application state. Hosting MCP in-process lets tools reuse `api.state.interest_repository` and avoids another deployable service, database connection, or configuration boundary.

   Alternative considered: a separate MCP service/container. That gives stronger isolation and independent scaling, but it duplicates app wiring and is unnecessary for a personal interest-management surface.

2. Use remote Streamable HTTP at `/mcp`.

   Users need a URL that AI agents can connect to for local or deployed apps. Streamable HTTP is the standard remote MCP transport and fits the existing web service deployment model.

   Alternative considered: stdio-only MCP. That is simpler for local desktop clients, but it does not fit Render or hosted agent connections.

3. Use the official Python MCP SDK.

   The backend should own tool behavior, not custom MCP protocol details. The SDK should handle initialization, JSON-RPC message handling, content types, and Streamable HTTP behavior.

   Alternative considered: hand-roll JSON-RPC inside FastAPI. That avoids a dependency but risks protocol drift and subtle compatibility bugs.

4. Protect MCP with a single bearer token.

   `MCP_AUTH_TOKEN` is required before MCP is usable. Requests must include `Authorization: Bearer <token>`. If the setting is missing, `/mcp` returns a clear 503-style misconfiguration response.

   Alternative considered: unauthenticated local development fallback. That creates a risky split-brain behavior and could expose writes if misconfigured in deployment.

5. Validate browser origins only when an `Origin` header is present.

   Browser-origin requests must match `MCP_ALLOWED_ORIGINS`; if the setting is empty, requests with `Origin` are rejected. Requests without `Origin`, such as CLI, IDE, or server-side MCP clients, rely on bearer-token authentication.

   Alternative considered: require allowed origins for all MCP traffic. That adds friction for non-browser clients without improving the browser-origin attack case.

6. Add a backend command layer for MCP tools.

   MCP tools should call reusable application functions that read the current payload, apply one targeted change, validate the resulting `InterestsPayload`, and write through `InterestRepository`. This keeps agent writes behind the existing persistence boundary while avoiding raw full-document replacement.

   Alternative considered: expose `save_interests` as one MCP tool. That is thin, but it makes agents responsible for preserving every interest/source and increases data-loss risk.

7. Require IDs for writes and return IDs from reads/creates.

   `list_interests` returns IDs and names for interests and sources. Write operations accept stable IDs only. Create tools generate IDs server-side and return the created object.

   Alternative considered: exact name/label lookup for writes. That is convenient, but names and labels are user-facing and not guaranteed unique.

8. Keep strict domain validation.

   Tool input should use Pydantic schemas and existing domain models. Invalid priorities, source types, missing required fields, duplicate IDs, or malformed soft-delete timestamps should return explicit tool errors. The tools should not infer source types or add quiet fallbacks.

9. Preserve soft-delete semantics.

   MCP delete/remove operations set `deletedAt` on interests or sources. List tools should exclude deleted records by default and optionally include them when requested.

10. Keep Render changes operational but secret-free.

   `render.yaml` should declare `MCP_AUTH_TOKEN` and `MCP_ALLOWED_ORIGINS` as dashboard-managed values. Docs should explain the backend `/mcp` URL, bearer token header, and origin behavior.

## Risks / Trade-offs

- MCP broadens the backend's public write surface -> Require explicit token configuration, bearer auth, and origin checks for browser requests.
- A single bearer token is coarse-grained -> Keep v1 scoped to personal app use and document that multi-user/per-agent authorization is out of scope.
- Command tools duplicate some frontend editing behavior -> Put command logic in backend application code so MCP tools share one server-side path and future HTTP command endpoints can reuse it.
- Python MCP SDK integration may not fit FastAPI mounting exactly as expected -> Isolate MCP wiring in a presentation module and cover configured/unconfigured behavior with tests.
- Server-side ID generation diverges from current frontend-created IDs -> Limit the change to MCP-created records for now and return generated IDs in tool responses.
- Soft-deleted records can accumulate -> Keep behavior consistent with existing UI and leave cleanup/restore flows for a future change.
