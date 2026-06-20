## Purpose

Define saved update collections, saved update snapshot behavior, and collection membership operations.

## Requirements

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

### Requirement: Saved updates preserve snapshots
The system SHALL display saved collection updates from the stored snapshot rather than requiring the update to be collected again from its source.

#### Scenario: Source update is no longer present in collected results
- **WHEN** a saved update no longer appears in a later `/api/updates` response
- **THEN** the Collections page still displays the saved update using the persisted snapshot fields

#### Scenario: Source metadata changes after save
- **WHEN** the title, image, summary, published time, or source metadata changes in later source collection results
- **THEN** the saved collection entry keeps displaying the snapshot values captured when the update was first saved

### Requirement: Saved updates are ordered by save time
The system SHALL order saved updates in each collection by the time they were saved, newest first.

#### Scenario: Multiple updates are saved to one collection
- **WHEN** the user views a collection containing multiple saved updates
- **THEN** the saved updates appear in descending `saved_at` order

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

### Requirement: Saved updates can be removed from a collection
The system SHALL allow a saved update to be removed from a collection by collection id and deterministic update key.

#### Scenario: User removes a saved update
- **WHEN** the user removes a saved update from a collection
- **THEN** the saved update no longer appears in that collection

#### Scenario: User removes an update from one collection only
- **WHEN** the same update key is saved in both fixed collections and the user removes it from one
- **THEN** the saved update remains visible in the other collection

### Requirement: Unknown collections are rejected
The system SHALL reject save and remove requests for collection ids other than the fixed collections.

#### Scenario: Client saves to an unknown collection
- **WHEN** the client requests to save an update to an unknown collection id
- **THEN** the system rejects the request without storing a saved update

#### Scenario: Client removes from an unknown collection
- **WHEN** the client requests to remove an update from an unknown collection id
- **THEN** the system rejects the request without changing saved updates

### Requirement: Collections can be filtered by source type
The Collections page SHALL allow users to filter saved update items by source type while preserving the all-source default view.

#### Scenario: All saved source types are visible by default
- **WHEN** the Collections page has loaded saved updates from multiple source types
- **THEN** each collection displays saved updates from every loaded source type before the user changes the source type filter

#### Scenario: User filters saved updates by source type
- **WHEN** the user selects a specific source type on the Collections page
- **THEN** each collection displays only saved updates whose update snapshot `source_interest.source_type` matches the selected source type

#### Scenario: Fixed collections remain visible
- **WHEN** the user selects a source type that has no saved updates in one fixed collection
- **THEN** that fixed collection remains visible with an empty saved-update state for the selected filter
