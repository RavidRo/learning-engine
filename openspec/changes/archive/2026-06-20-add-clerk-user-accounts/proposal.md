# Proposal: Clerk User Accounts

## Why

Signal Garden currently stores interests, collections, and MCP writes in one global application data set. RAV-18 makes the app usable by multiple people by adding Clerk authentication and scoping each user's data to their signed-in identity.

## What Changes

- Add Clerk sign-in, sign-up, and signed-in user controls to the React/Vite webapp.
- Require an authenticated Clerk session before loading or mutating user data.
- Verify Clerk session tokens in the FastAPI backend through a thin authentication boundary that produces app-owned `{user_id}` context.
- Scope interests, update collection data, update cache keys, import/export behavior, and MCP operations by authenticated user.
- Replace the single global `MCP_AUTH_TOKEN` write model with authenticated MCP requests that resolve to the same user context used by the HTTP API.
- **BREAKING**: anonymous HTTP clients can no longer access `/api/interests`, `/api/updates`, `/api/collections`, interest import/export, or collection write operations.
- **BREAKING**: MCP clients can no longer use one shared backend bearer token for all users.

## Capabilities

### New Capabilities
- `authentication-user-accounts`: Clerk-backed user authentication, backend token verification, and user context behavior.

### Modified Capabilities
- `interests`: Interest read, write, import, and export operations become authenticated and user-scoped.
- `collections`: Saved update collections become authenticated and user-scoped.
- `updates`: Update collection reads use only the authenticated user's interests and cache entries.
- `mcp`: MCP authentication resolves user context instead of accepting one global bearer token for all users.
- `webapp-shell`: The shell exposes authenticated user controls and gates app data views until a session is available.

## Impact

- Backend presentation layer: FastAPI dependencies/middleware for Clerk token verification and user context injection.
- Backend application ports and storage: repository operations gain user context, and relational rows/unique constraints include user ownership.
- Backend MCP presentation: authentication and tool execution use user context rather than `MCP_AUTH_TOKEN`.
- Frontend: Clerk React SDK, environment configuration, authenticated fetch wrapper, and signed-out/signed-in states.
- Deployment/docs: Clerk publishable/secret/JWKS configuration replaces the global MCP token instructions for multi-user access.
- Tests: backend auth verification, unauthorized rejection, user isolation for interests and collections, user-scoped update cache behavior, MCP authorization, and frontend authenticated states.
