## 1. Auth Setup

- [x] 1.1 Add Clerk frontend and backend dependencies/configuration without committing secret values.
- [x] 1.2 Define backend `UserContext` and Clerk verification boundary that returns provider-neutral `user_id`.
- [x] 1.3 Add backend tests for valid token, missing token, and invalid token outcomes.
- [x] 1.4 Add protected-route dependency wiring for FastAPI routes that access user data.

## 2. Persistence And Application Boundaries

- [x] 2.1 Decide and document the bootstrap Clerk user id/backfill path for existing global data.
- [x] 2.2 Add user ownership columns, indexes, and uniqueness constraints to interest, source, collection, and saved update storage models.
- [x] 2.3 Update `InterestRepository` and `CollectionRepository` ports to require user context for user-owned operations.
- [x] 2.4 Update storage adapter reads, writes, fixed collection initialization, and import/export replacement to apply user predicates.
- [x] 2.5 Add repository tests proving two users cannot read, overwrite, import, export, save, or remove each other's data.

## 3. HTTP API And Updates

- [x] 3.1 Protect interest read/write/import/export routes and pass user context into repository calls.
- [x] 3.2 Protect collection list/save/remove routes and pass user context into collection application services.
- [x] 3.3 Protect updates route and collect updates from the authenticated user's interests only.
- [x] 3.4 Include user id in update cache scopes and add tests for cross-user cache isolation.
- [x] 3.5 Ensure anonymous and invalid-token requests return clear errors without invoking data operations.

## 4. MCP

- [x] 4.1 Replace `MCP_AUTH_TOKEN` request authentication with Clerk session bearer verification.
- [x] 4.2 Pass user context into all MCP interest/source listing and write tools.
- [x] 4.3 Preserve MCP host and origin validation while updating configuration names and error messages for Clerk auth.
- [x] 4.4 Add MCP tests for missing token, invalid token, user-scoped listing, and cross-user write attempts.

## 5. Webapp

- [x] 5.1 Initialize `@clerk/react` at the app entry point using `VITE_CLERK_PUBLISHABLE_KEY`.
- [x] 5.2 Add sign-in, sign-up, and signed-in user controls to the existing top navigation/shell.
- [x] 5.3 Gate user data views until the user is signed in.
- [x] 5.4 Add an authenticated fetch helper that obtains Clerk session tokens and attaches `Authorization: Bearer <token>` to user API requests.
- [x] 5.5 Invalidate and reload user data queries when the signed-in session changes.
- [x] 5.6 Add frontend tests or component coverage for signed-out, signed-in, and token-unavailable states.
- [x] 5.7 Add signed-in account controls that let users copy a current Clerk session token for MCP setup without storing it in app data.

## 6. Deployment, Docs, And Verification

- [x] 6.1 Update Render configuration and deployment docs for Clerk frontend/backend settings and remove global MCP token setup.
- [x] 6.2 Update MCP client docs to explain Clerk session bearer token requirements.
- [x] 6.3 Run focused backend auth/storage/MCP tests during implementation.
- [x] 6.4 Run focused web checks for the authenticated shell and API client changes.
- [x] 6.5 Run `task check` before finishing when feasible.
