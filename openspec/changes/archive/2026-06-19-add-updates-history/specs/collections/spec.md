## MODIFIED Requirements

### Requirement: Fixed collections are available
The system SHALL provide the fixed collections `See Later`, `Liked`, and `History` without requiring the user to create them.

#### Scenario: Collections are listed before any updates are saved
- **WHEN** the user opens the Collections page or the client requests collections
- **THEN** the system returns `See Later`, `Liked`, and `History` collections with stable ids and empty saved update lists

#### Scenario: Data store is initialized more than once
- **WHEN** the backend ensures the collection data store repeatedly
- **THEN** the system preserves exactly one row for each fixed collection

### Requirement: Updates can be saved to a collection
The system SHALL allow a visible update snapshot to be saved into any fixed collection.

#### Scenario: User saves an update to See Later
- **WHEN** the user saves a visible update to the `See Later` collection
- **THEN** the system stores that update in `See Later` with a deterministic update key, the update snapshot, and the current save timestamp

#### Scenario: User saves an update to Liked
- **WHEN** the user saves a visible update to the `Liked` collection
- **THEN** the system stores that update in `Liked` with a deterministic update key, the update snapshot, and the current save timestamp

#### Scenario: User checks out an update
- **WHEN** the user clicks a visible update link
- **THEN** the system stores that update in `History` with a deterministic update key, the update snapshot, and the current save timestamp

### Requirement: Saving the same update is idempotent
The system SHALL prevent duplicate entries for the same deterministic update key within a collection.

#### Scenario: User saves the same update to the same collection twice
- **WHEN** the user saves an update that already exists in the target collection
- **THEN** the system returns the existing saved update without adding a duplicate and without changing its original save timestamp

#### Scenario: User checks out the same update twice
- **WHEN** the user clicks an update link that already exists in `History`
- **THEN** the system returns the existing saved update without adding a duplicate and without changing its original history timestamp

#### Scenario: User saves the same update to a different collection
- **WHEN** the same update exists in one fixed collection and is saved to another fixed collection
- **THEN** the system stores a distinct saved entry in the second collection with its own save timestamp
