## ADDED Requirements

### Requirement: Updates require user context
The system SHALL require authenticated user context before collecting updates.

#### Scenario: Authenticated user requests updates
- **WHEN** a signed-in user requests updates
- **THEN** the system collects updates using only interests and sources owned by that user

#### Scenario: Anonymous user requests updates
- **WHEN** an anonymous request tries to fetch updates
- **THEN** the system rejects the request without collecting source updates

### Requirement: Updates cache is user-scoped
The system SHALL scope cached update collection results by authenticated user and update request window.

#### Scenario: Two users request the same update window
- **WHEN** two different users request updates for the same time window
- **THEN** cached results from one user are not reused for the other user

#### Scenario: Same user refreshes the same update window
- **WHEN** the same signed-in user requests the same update window while cache entries are fresh
- **THEN** the system can reuse that user's cached source update results
