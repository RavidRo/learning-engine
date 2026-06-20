## ADDED Requirements

### Requirement: Collections require user context
The system SHALL require authenticated user context for collection list, save, and remove operations.

#### Scenario: Authenticated user lists collections
- **WHEN** a signed-in user requests collections
- **THEN** the system returns fixed collections and saved updates for that user only

#### Scenario: Anonymous user lists collections
- **WHEN** an anonymous request tries to list collections
- **THEN** the system rejects the request without returning collection data

#### Scenario: Authenticated user saves an update
- **WHEN** a signed-in user saves an update to a fixed collection
- **THEN** the saved update is stored only in that user's collection

#### Scenario: Authenticated user removes an update
- **WHEN** a signed-in user removes an update from a fixed collection
- **THEN** the update is removed only from that user's collection

### Requirement: Fixed collections are user-scoped
The system SHALL provide the fixed collections `See Later`, `Liked`, and `History` independently for each authenticated user.

#### Scenario: New user lists collections
- **WHEN** a signed-in user lists collections before saving any updates
- **THEN** the system returns `See Later`, `Liked`, and `History` for that user with empty saved update lists

#### Scenario: Two users save the same update
- **WHEN** two different users save the same deterministic update key to the same fixed collection
- **THEN** each user has a distinct saved collection entry isolated from the other user

#### Scenario: Data store is initialized for multiple users
- **WHEN** the backend ensures collection data for multiple users
- **THEN** each user has exactly one row for each fixed collection
