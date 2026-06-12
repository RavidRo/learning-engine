## Why

Users should be able to connect an AI agent to the Learning Engine and manage their interests without manually editing the web UI. MCP provides a standard agent integration surface, but interest writes need guardrails so agents cannot accidentally replace or delete the full interest set.

## What Changes

- Add an authenticated MCP server endpoint to the existing FastAPI backend process at `/mcp` using Streamable HTTP.
- Protect MCP requests with a required `MCP_AUTH_TOKEN` bearer token; return a clear service-unavailable response when MCP is not configured.
- Validate browser-origin MCP requests with an explicit `MCP_ALLOWED_ORIGINS` allowlist.
- Expose command-style interest management tools for listing interests, creating/updating/pausing/resuming/soft-deleting interests, and adding/updating/pausing/resuming/soft-deleting sources.
- Generate IDs server-side for MCP-created interests and sources, and require stable IDs for all MCP write operations.
- Use strict backend validation and existing domain normalization for priorities, source types, URLs, labels, descriptions, enabled flags, and soft-deletion timestamps.
- Update Render configuration and deployment documentation for MCP environment variables and the `/mcp` connection URL.

## Capabilities

### New Capabilities

- `mcp-interest-management`: Authenticated MCP access for AI agents to manage interests and sources through safe command-style tools.

### Modified Capabilities

- None.

## Impact

- Backend presentation layer: mount or route the MCP Streamable HTTP endpoint inside the existing FastAPI app.
- Backend application/domain layer: add reusable command-style interest/source operations behind the existing `InterestRepository` port.
- Backend configuration: add `MCP_AUTH_TOKEN` and `MCP_ALLOWED_ORIGINS` settings.
- Backend dependencies: add the official Python MCP SDK.
- Tests: cover MCP auth/configuration behavior, origin validation, tool schemas, command behavior, validation failures, ID generation, and soft-delete semantics.
- Deployment: document and configure Render environment variables without committing secret values.
