## ADDED Requirements

### Requirement: Authenticated MCP endpoint
The system SHALL expose a remote MCP Streamable HTTP endpoint at `/mcp` from the existing FastAPI backend process when MCP is configured.

#### Scenario: MCP token is configured
- **WHEN** the backend starts with `MCP_AUTH_TOKEN` configured
- **THEN** `/mcp` accepts MCP Streamable HTTP requests that include a matching bearer token

#### Scenario: MCP token is missing
- **WHEN** the backend receives a request for `/mcp` without `MCP_AUTH_TOKEN` configured
- **THEN** the response indicates that MCP is unavailable because it is not configured

#### Scenario: Bearer token is missing or invalid
- **WHEN** the backend receives an MCP request without a matching `Authorization: Bearer <token>` header
- **THEN** the request is rejected without invoking an MCP tool

### Requirement: MCP browser-origin validation
The system SHALL validate the `Origin` header for browser-origin MCP requests using `MCP_ALLOWED_ORIGINS`.

#### Scenario: Browser origin is allowed
- **WHEN** an MCP request includes an `Origin` header listed in `MCP_ALLOWED_ORIGINS` and a valid bearer token
- **THEN** the request is allowed to continue to MCP protocol handling

#### Scenario: Browser origin is not allowed
- **WHEN** an MCP request includes an `Origin` header that is not listed in `MCP_ALLOWED_ORIGINS`
- **THEN** the request is rejected without invoking an MCP tool

#### Scenario: Browser origin allowlist is unset
- **WHEN** an MCP request includes an `Origin` header and `MCP_ALLOWED_ORIGINS` is empty
- **THEN** the request is rejected without invoking an MCP tool

#### Scenario: Non-browser client omits origin
- **WHEN** an MCP request has no `Origin` header and includes a valid bearer token
- **THEN** the request is not rejected for missing `MCP_ALLOWED_ORIGINS`

### Requirement: MCP interest listing
The system SHALL provide an MCP tool that lists interests and their sources with stable IDs and human-readable names.

#### Scenario: List active interests
- **WHEN** an agent calls `list_interests` without requesting deleted records
- **THEN** the tool returns non-deleted interests with each interest ID, name, enabled state, priority, description, and non-deleted source IDs, labels, types, URLs, enabled states, image URLs, and ignore keywords

#### Scenario: Include deleted records
- **WHEN** an agent calls `list_interests` with deleted records included
- **THEN** the tool returns deleted interests and sources with their `deletedAt` values

### Requirement: MCP command-style interest writes
The system SHALL provide MCP tools for creating, updating, pausing, resuming, and soft-deleting interests without exposing raw full-payload replacement.

#### Scenario: Create interest
- **WHEN** an agent creates an interest with valid name, description, priority, enabled state, and at least one valid source
- **THEN** the system generates stable IDs for the new interest and sources, persists the interest through the interest repository, and returns the created interest

#### Scenario: Update interest by ID
- **WHEN** an agent updates an existing non-deleted interest using its interest ID and valid field values
- **THEN** only that interest's fields are changed and the other persisted interests are preserved

#### Scenario: Pause interest by ID
- **WHEN** an agent pauses an existing non-deleted interest using its interest ID
- **THEN** that interest is persisted with `enabled` set to false

#### Scenario: Resume interest by ID
- **WHEN** an agent resumes an existing non-deleted interest using its interest ID
- **THEN** that interest is persisted with `enabled` set to true

#### Scenario: Soft-delete interest by ID
- **WHEN** an agent deletes an existing non-deleted interest using its interest ID
- **THEN** that interest is persisted with a `deletedAt` timestamp and is excluded from default interest listings

#### Scenario: Missing interest ID
- **WHEN** an agent requests a write for an interest ID that does not identify an existing non-deleted interest
- **THEN** the tool returns a clear not-found error and does not write a modified payload

### Requirement: MCP command-style source writes
The system SHALL provide MCP tools for adding, updating, pausing, resuming, and soft-deleting sources by stable interest and source IDs.

#### Scenario: Add source
- **WHEN** an agent adds a valid source to an existing non-deleted interest using the interest ID
- **THEN** the system generates a stable source ID, persists the source on that interest, and returns the created source

#### Scenario: Update source by ID
- **WHEN** an agent updates an existing non-deleted source using its interest ID, source ID, and valid field values
- **THEN** only that source's fields are changed and the other sources and interests are preserved

#### Scenario: Pause source by ID
- **WHEN** an agent pauses an existing non-deleted source using its interest ID and source ID
- **THEN** that source is persisted with `enabled` set to false

#### Scenario: Resume source by ID
- **WHEN** an agent resumes an existing non-deleted source using its interest ID and source ID
- **THEN** that source is persisted with `enabled` set to true

#### Scenario: Soft-delete source by ID
- **WHEN** an agent removes an existing non-deleted source using its interest ID and source ID
- **THEN** that source is persisted with a `deletedAt` timestamp and is excluded from default interest listings

#### Scenario: Missing source ID
- **WHEN** an agent requests a write for a source ID that does not identify an existing non-deleted source on the target interest
- **THEN** the tool returns a clear not-found error and does not write a modified payload

### Requirement: MCP validation and persistence boundaries
The system SHALL validate MCP tool input through backend schemas and domain models, and SHALL persist changes only through the existing interest repository.

#### Scenario: Invalid tool input
- **WHEN** an agent calls an MCP write tool with an invalid priority, source type, missing required source URL, duplicate generated ID, or otherwise invalid interest payload
- **THEN** the tool returns a validation error and does not write a modified payload

#### Scenario: Existing domain normalization applies
- **WHEN** an agent calls an MCP write tool with values that the existing domain models normalize, such as surrounding whitespace
- **THEN** the persisted payload uses the normalized domain values

#### Scenario: Repository boundary is used
- **WHEN** an MCP write tool persists a valid change
- **THEN** the change is written through `InterestRepository.write_interests`

### Requirement: MCP deployment configuration
The system SHALL document and configure deployment settings needed to operate the MCP interest-management endpoint.

#### Scenario: Render configuration declares MCP variables
- **WHEN** the Render blueprint is inspected
- **THEN** it declares `MCP_AUTH_TOKEN` and `MCP_ALLOWED_ORIGINS` as environment variables without committing secret values

#### Scenario: Deployment docs explain agent connection
- **WHEN** a user reads the deployment documentation
- **THEN** the docs describe the `/mcp` endpoint URL, bearer token requirement, missing-token behavior, and browser-origin allowlist behavior
