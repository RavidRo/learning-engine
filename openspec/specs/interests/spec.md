## Purpose

Define interest data management, including user-facing backup and restore behavior.

## Requirements

### Requirement: Export interests as versioned JSON

The system SHALL allow users to export all stored interests as a JSON file using a versioned export envelope.

#### Scenario: Export includes complete stored interest payload

- **WHEN** the user requests an interest export
- **THEN** the system returns a JSON envelope with `schemaVersion` set to `1`
- **AND** the envelope includes an `exportedAt` timestamp
- **AND** the envelope includes every stored interest from the repository, including disabled and soft-deleted interests

#### Scenario: Export does not expose unrelated data

- **WHEN** the user exports interests
- **THEN** the export file includes interest and source data only
- **AND** the export file excludes collected updates, caches, and other non-interest state

### Requirement: Import versioned JSON as full replacement

The system SHALL allow users to import a version 1 interest export envelope as a full replacement for the current stored interest list.

#### Scenario: Valid import replaces current interests

- **WHEN** the user imports a valid version 1 interest export envelope
- **THEN** the system validates the envelope and nested interests
- **AND** the system replaces the entire stored interest list with the imported interests
- **AND** the user sees the imported active interests after the import completes

#### Scenario: Invalid import does not change stored interests

- **WHEN** the user imports malformed JSON, an unsupported schema version, or an envelope with invalid interests
- **THEN** the system rejects the import with an error
- **AND** the current stored interest list remains unchanged

#### Scenario: Raw interest payload is rejected by import endpoint

- **WHEN** the user imports a raw `{ "interests": [...] }` payload without the required versioned envelope fields
- **THEN** the system rejects the import with an error
- **AND** the current stored interest list remains unchanged

### Requirement: Import action requires explicit replacement confirmation

The system SHALL require explicit user confirmation before uploading an interest import file that will replace the current stored interest list.

#### Scenario: User cancels replacement confirmation

- **WHEN** the user selects an import file and cancels the replacement confirmation
- **THEN** the system does not upload the file
- **AND** the current stored interest list remains unchanged

#### Scenario: User confirms replacement

- **WHEN** the user selects an import file and confirms replacement
- **THEN** the system uploads the file to the import endpoint
- **AND** the displayed interest list refreshes from the imported saved payload after a successful import
