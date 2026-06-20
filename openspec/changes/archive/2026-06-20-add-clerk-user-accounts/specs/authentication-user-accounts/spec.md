# Authentication User Accounts

## ADDED Requirements

### Requirement: Clerk session authentication
The system SHALL require a valid Clerk session before any user data API or MCP tool can access user-owned data.

#### Scenario: Request includes a valid session token
- **WHEN** a protected API or MCP request includes a valid Clerk session token
- **THEN** the backend authenticates the request and continues only after deriving app-owned user context

#### Scenario: Request is anonymous
- **WHEN** a protected API or MCP request omits authentication credentials
- **THEN** the backend rejects the request without reading or writing user-owned data

#### Scenario: Request includes an invalid session token
- **WHEN** a protected API or MCP request includes an expired, malformed, or unverifiable Clerk session token
- **THEN** the backend rejects the request without reading or writing user-owned data

### Requirement: User identity owns application data
The system SHALL use the authenticated Clerk user id as the owner for interests, collections, updates cache entries, imports, exports, and MCP operations.

#### Scenario: Authenticated user context is derived
- **WHEN** an authenticated request resolves to a Clerk user
- **THEN** the backend exposes `user_id` as provider-neutral user context to application services

#### Scenario: User signs in on another device
- **WHEN** the same Clerk user signs in from another browser or device
- **THEN** the app loads the same user-owned interests and collections for that user

#### Scenario: Different user signs in
- **WHEN** a different Clerk user signs in
- **THEN** the app loads data owned by that different user only

### Requirement: Provider-specific state stays at the boundary
The system SHALL keep Clerk-specific request/session objects out of application services and repository implementations.

#### Scenario: Application service receives auth context
- **WHEN** a protected route or MCP tool calls an application service
- **THEN** it passes app-owned user context rather than provider-specific Clerk objects

#### Scenario: Token verification is tested
- **WHEN** backend tests cover authentication behavior
- **THEN** they verify valid-token, invalid-token, and missing-token outcomes at the auth boundary

### Requirement: User data isolation
The system SHALL prevent one authenticated user from reading, mutating, importing, exporting, or caching another user's data.

#### Scenario: Two users have interests
- **WHEN** two different authenticated users request interests
- **THEN** each user receives only the interests owned by their own Clerk user id

#### Scenario: One user writes data
- **WHEN** one authenticated user creates, updates, imports, or deletes data
- **THEN** data owned by other users is unchanged

#### Scenario: Process-wide cache is used
- **WHEN** user-specific data is cached in backend process memory
- **THEN** the cache key includes the authenticated user id so cached results are not shared across users
