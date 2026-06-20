## MODIFIED Requirements

### Requirement: Authenticated MCP endpoint
The system SHALL expose a remote MCP Streamable HTTP endpoint at `/mcp` from the existing FastAPI backend process for authenticated Clerk users.

#### Scenario: Clerk session token is valid
- **WHEN** the backend receives an MCP request with a valid Clerk session bearer token
- **THEN** `/mcp` accepts the request and continues to MCP protocol handling with user context

#### Scenario: Clerk session token is missing
- **WHEN** the backend receives an MCP request without a bearer token
- **THEN** the request is rejected without invoking an MCP tool

#### Scenario: Clerk session token is invalid
- **WHEN** the backend receives an MCP request with an expired, malformed, or unverifiable Clerk session bearer token
- **THEN** the request is rejected without invoking an MCP tool

### Requirement: MCP interest listing
The system SHALL provide an MCP tool that lists interests and their sources with stable IDs and human-readable names for the authenticated user.

#### Scenario: List active interests
- **WHEN** an authenticated user agent calls `list_interests` without requesting deleted records
- **THEN** the tool returns non-deleted interests owned by the authenticated user with each interest ID, name, enabled state, priority, description, and non-deleted source IDs, labels, types, URLs, enabled states, image URLs, and ignore keywords

#### Scenario: Include deleted records
- **WHEN** an authenticated user agent calls `list_interests` with deleted records included
- **THEN** the tool returns deleted interests and sources owned by the authenticated user with their `deletedAt` values

#### Scenario: Other users have interests
- **WHEN** an authenticated user agent lists interests and other users have stored interests
- **THEN** the tool excludes interests and sources owned by other users

### Requirement: MCP command-style interest writes
The system SHALL provide MCP tools for creating, updating, pausing, resuming, and soft-deleting interests within the authenticated user's data without exposing raw full-payload replacement.

#### Scenario: Create interest
- **WHEN** an authenticated user agent creates an interest with valid name, description, priority, enabled state, and at least one valid source
- **THEN** the system generates stable IDs for the new interest and sources, persists the interest through the interest repository for the authenticated user, and returns the created interest

#### Scenario: Update interest by ID
- **WHEN** an authenticated user agent updates an existing non-deleted interest owned by that user using its interest ID and valid field values
- **THEN** only that interest's fields are changed and the other persisted interests are preserved

#### Scenario: Pause interest by ID
- **WHEN** an authenticated user agent pauses an existing non-deleted interest owned by that user using its interest ID
- **THEN** that interest is persisted with `enabled` set to false

#### Scenario: Resume interest by ID
- **WHEN** an authenticated user agent resumes an existing non-deleted interest owned by that user using its interest ID
- **THEN** that interest is persisted with `enabled` set to true

#### Scenario: Soft-delete interest by ID
- **WHEN** an authenticated user agent deletes an existing non-deleted interest owned by that user using its interest ID
- **THEN** that interest is persisted with a `deletedAt` timestamp and is excluded from default interest listings

#### Scenario: Missing interest ID
- **WHEN** an authenticated user agent requests a write for an interest ID that does not identify an existing non-deleted interest owned by that user
- **THEN** the tool returns a clear not-found error and does not write a modified payload

#### Scenario: Interest ID belongs to another user
- **WHEN** an authenticated user agent requests a write for an interest ID owned by another user
- **THEN** the tool behaves as not found and does not write a modified payload

### Requirement: MCP command-style source writes
The system SHALL provide MCP tools for adding, updating, pausing, resuming, and soft-deleting sources by stable interest and source IDs within the authenticated user's data.

#### Scenario: Add source
- **WHEN** an authenticated user agent adds a valid source to an existing non-deleted interest owned by that user using the interest ID
- **THEN** the system generates a stable source ID, persists the source on that interest, and returns the created source

#### Scenario: Update source by ID
- **WHEN** an authenticated user agent updates an existing non-deleted source owned by that user using its interest ID, source ID, and valid field values
- **THEN** only that source's fields are changed and the other sources and interests are preserved

#### Scenario: Pause source by ID
- **WHEN** an authenticated user agent pauses an existing non-deleted source owned by that user using its interest ID and source ID
- **THEN** that source is persisted with `enabled` set to false

#### Scenario: Resume source by ID
- **WHEN** an authenticated user agent resumes an existing non-deleted source owned by that user using its interest ID and source ID
- **THEN** that source is persisted with `enabled` set to true

#### Scenario: Soft-delete source by ID
- **WHEN** an authenticated user agent removes an existing non-deleted source owned by that user using its interest ID and source ID
- **THEN** that source is persisted with a `deletedAt` timestamp and is excluded from default interest listings

#### Scenario: Missing source ID
- **WHEN** an authenticated user agent requests a write for an interest ID and source ID that do not identify an existing non-deleted source owned by that user
- **THEN** the tool returns a clear not-found error and does not write a modified payload

#### Scenario: Source ID belongs to another user
- **WHEN** an authenticated user agent requests a write for a source ID owned by another user
- **THEN** the tool behaves as not found and does not write a modified payload

### Requirement: MCP validation and persistence boundaries
The system SHALL validate MCP tool input through backend schemas and domain models, and SHALL persist changes only through the existing interest repository with user context.

#### Scenario: Invalid tool input
- **WHEN** an authenticated user agent calls an MCP write tool with an invalid priority, source type, missing required source URL, duplicate generated ID, or otherwise invalid interest payload
- **THEN** the tool returns a validation error and does not write a modified payload

#### Scenario: Existing domain normalization applies
- **WHEN** an authenticated user agent calls an MCP write tool with values that the existing domain models normalize, such as surrounding whitespace
- **THEN** the persisted payload uses the normalized domain values

#### Scenario: Repository boundary is used
- **WHEN** an MCP write tool persists a valid change
- **THEN** the change is written through `InterestRepository.write_interests` with user context

### Requirement: MCP deployment configuration
The system SHALL document and configure deployment settings needed to operate the MCP interest-management endpoint with Clerk authentication.

#### Scenario: Render configuration declares MCP auth variables
- **WHEN** the Render blueprint is inspected
- **THEN** it declares Clerk backend authentication configuration and MCP host/origin allowlist variables without committing secret values

#### Scenario: Deployment docs explain agent connection
- **WHEN** a user reads the deployment documentation
- **THEN** the docs describe the `/mcp` endpoint URL, Clerk session bearer token requirement, host allowlist behavior, and browser-origin allowlist behavior
