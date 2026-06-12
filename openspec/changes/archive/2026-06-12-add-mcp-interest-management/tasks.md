## 1. Backend Configuration and Dependency

- [x] 1.1 Add the official Python MCP SDK dependency to `backend/pyproject.toml` and refresh `backend/uv.lock`.
- [x] 1.2 Add `mcp_auth_token()` and `mcp_allowed_origins()` configuration helpers that trim values and parse comma-separated origins.
- [x] 1.3 Add focused tests for MCP configuration parsing, including missing token, blank token, empty origins, and multiple origins.

## 2. Interest Management Command Layer

- [x] 2.1 Add backend schemas or command input models for MCP interest and source operations.
- [x] 2.2 Implement server-side ID generation for MCP-created interests and sources with duplicate-ID protection.
- [x] 2.3 Implement `list_interests` command behavior with default deleted-record filtering and optional deleted-record inclusion.
- [x] 2.4 Implement create, update, pause, resume, and soft-delete commands for interests using interest IDs.
- [x] 2.5 Implement add, update, pause, resume, and soft-delete commands for sources using interest and source IDs.
- [x] 2.6 Ensure all commands validate through existing domain models and write only through `InterestRepository.write_interests`.
- [x] 2.7 Add application-layer tests for successful commands, not-found errors, validation errors, soft-delete timestamps, ID generation, and preservation of unrelated records.

## 3. MCP Server Integration

- [x] 3.1 Create a presentation module that registers MCP tools for interest management using the official Python MCP SDK.
- [x] 3.2 Mount or route the MCP Streamable HTTP endpoint at `/mcp` inside the existing FastAPI app lifecycle.
- [x] 3.3 Wire MCP tools to the existing app `InterestRepository` state rather than creating a separate persistence path.
- [x] 3.4 Add bearer-token authentication for every `/mcp` request and prevent tool invocation when the token is missing or invalid.
- [x] 3.5 Return a clear service-unavailable response from `/mcp` when `MCP_AUTH_TOKEN` is not configured.
- [x] 3.6 Add `Origin` validation for `/mcp` requests that include an `Origin` header, using `MCP_ALLOWED_ORIGINS`.
- [x] 3.7 Add presentation tests for configured MCP access, missing configuration, invalid/missing bearer token, allowed origin, rejected origin, unset origins with browser request, and no-origin non-browser request.

## 4. Deployment and Documentation

- [x] 4.1 Add `MCP_AUTH_TOKEN` to `render.yaml` as an unset Render-managed secret value.
- [x] 4.2 Add `MCP_ALLOWED_ORIGINS` to `render.yaml` as an unset Render-managed environment value.
- [x] 4.3 Update deployment documentation with the `/mcp` URL, bearer token setup, missing-token behavior, and browser-origin allowlist behavior.
- [x] 4.4 Document the v1 MCP tool scope and explicitly note that update collection and briefing retrieval are out of scope.

## 5. Verification

- [x] 5.1 Run the narrowest backend tests for the MCP command layer and MCP presentation/auth behavior.
- [x] 5.2 Run backend linting and type checking for the changed backend modules.
- [x] 5.3 Run `task check` before finishing implementation, if feasible.
