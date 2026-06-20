## Context

RAV-18 moves Signal Garden from a single-user deployment model to a multi-user account model. The current FastAPI app wires one `DEFAULT_STORE` into every HTTP route and MCP tool, so interests, update collections, and update cache entries are shared globally. MCP is protected by one `MCP_AUTH_TOKEN`, which is intentionally coarse but cannot isolate different signed-in users.

The ticket selects Clerk as the identity provider. Clerk's React integration fits the existing Vite app through `@clerk/react`, and cross-origin backend requests can carry the Clerk session token in `Authorization: Bearer <token>`. The backend should verify that token at the presentation boundary and convert it into an app-owned user context before calling application services or persistence.

## Goals / Non-Goals

**Goals:**

- Require a valid Clerk session before any user data or MCP write operation can run.
- Keep Clerk-specific verification isolated in a backend auth adapter and frontend auth shell.
- Pass an app-owned `UserContext` containing `user_id` into repositories and application services.
- Scope interests, collections, import/export, update cache entries, and MCP tools by authenticated user.
- Remove reliance on one shared `MCP_AUTH_TOKEN` for all users.
- Cover authentication failures and user data isolation with backend tests.

**Non-Goals:**

- No Clerk organization, workspace, team, role, invitation, or B2B hierarchy model.
- No shared interests or shared collections between users.
- No custom authorization matrix beyond requiring the authenticated owner.
- No broad MCP surface expansion beyond making the existing interest-management tools user-scoped.
- No migration of source provider credentials to per-user secrets unless they are already persisted as user data during implementation.

## Decisions

1. Use Clerk user identity as the data owner.

   The app will scope all user-owned data by Clerk user id. A signed-in user sees only their interests, collections, updates, import/export payloads, and MCP writes. There is no organization requirement and no organization switching UI.

   Alternative considered: use Clerk organizations as tenants. That is appropriate for B2B workspaces, but it adds hierarchy, membership, and switching concepts the product does not need for RAV-18.

2. Isolate Clerk behind an authentication boundary.

   Backend presentation code will verify Clerk JWTs and produce a provider-neutral `UserContext(user_id)`. Application services and repositories will accept that context rather than reading Clerk claims directly.

   Alternative considered: pass Clerk request/session objects through routers and services. That is faster initially, but it spreads provider-specific state through the clean architecture layers and makes later authorization or testing harder.

3. Make repository ports user-aware.

   `InterestRepository` and `CollectionRepository` operations will require `UserContext` or a small user id value object for reads and writes. The storage adapter will apply user predicates on every query and include user ownership columns in uniqueness constraints.

   Alternative considered: create a per-request repository wrapper bound to a user and leave port methods unchanged. That hides an important dependency and makes it easier for new code to accidentally reuse an unscoped global repository. Explicit user context parameters are noisier but safer for this change.

4. Authenticate MCP with Clerk session bearer tokens.

   MCP requests will continue to use the `Authorization` header, but the bearer value must be a Clerk session token. MCP tools will execute with the same `UserContext` as HTTP routes.

   Alternative considered: keep `MCP_AUTH_TOKEN` and map it to one configured user. That preserves existing clients, but it does not satisfy the acceptance criterion that MCP auth no longer depends on one global token for all users.

5. Include user id in update cache scope.

   The source update TTL cache is process-wide today. Cache keys must include `user_id` and the request's time window so one user's interests cannot affect another user's update results.

   Alternative considered: disable caching for authenticated routes. That avoids leakage, but it gives up the existing performance behavior and is unnecessary if cache scope includes user identity.

## Risks / Trade-offs

- Clerk token verification or JWKS retrieval fails -> Return an explicit unauthorized or service-unavailable response at the auth boundary and do not call application services.
- Existing deployment data is global and unowned -> Add a migration/backfill step that assigns pre-existing rows to a configured bootstrap user, or fail deployment migration until the operator provides that user id.
- User ownership columns and constraints touch multiple tables -> Keep the migration focused on owner columns, indexes, and constraints; avoid unrelated storage refactors.
- MCP clients may not yet have an ergonomic Clerk login flow -> Document that MCP clients must provide a Clerk session bearer token and leave richer OAuth onboarding for a later ticket.
- Public API behavior becomes stricter -> Treat anonymous access removal as a breaking change and update frontend, docs, and tests together.

## Migration Plan

1. Add Clerk configuration without committing secrets: frontend publishable key, backend issuer/JWKS or secret configuration, and optional bootstrap user id for existing rows.
2. Add auth boundary tests using fake/verifiable tokens before wiring route protection.
3. Add user ownership columns and constraints to persistence models and migration/backfill logic.
4. Update repository ports, application services, HTTP routes, and MCP tools to require user context.
5. Update the webapp to initialize Clerk, require sign-in, show signed-in user controls, and attach session tokens to API requests.
6. Update deployment and MCP docs to remove global bearer token setup and explain Clerk user authentication requirements.
7. Run focused backend and web checks, then `task check` when feasible.

Rollback requires reverting the code deployment and database migration together. If user columns are added in a backward-compatible way before global reads are removed, rollback can keep the columns unused; after code starts enforcing user predicates, rollback must restore the previous global routes or provide a one-time data export first.

## Open Questions

- Which existing Clerk user id should own any already-deployed global data during the first migration?
