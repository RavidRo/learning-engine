## Purpose

Define how update publication timestamps are validated, stored in client state, rendered in the viewer's local timezone, and reported when invalid.

## Requirements

### Requirement: Update timestamps are adapted before rendering
The system SHALL validate update publication timestamps as ISO datetime strings immediately after fetching updates from the server and before passing update data to the updates page render path.

#### Scenario: Fetched timestamp is validated at the schema boundary
- **WHEN** the webapp receives an updates response containing an ISO datetime `published` timestamp
- **THEN** the update schema validates the timestamp and stores it as a `Date` before the updates page renders

#### Scenario: Timestamp with timezone is parsed
- **WHEN** the webapp receives an update with a valid ISO datetime `published` timestamp that includes timezone information
- **THEN** the adapted update data includes a `Date` value representing that instant

#### Scenario: Timestamp is missing
- **WHEN** the webapp receives an update without a `published` timestamp
- **THEN** the adapted update data has no publication timestamp and remains valid for rendering

#### Scenario: Timestamp cannot be parsed
- **WHEN** the webapp receives an update with a `published` timestamp that is not a valid ISO datetime
- **THEN** the updates fetch flow reports a user-visible error instead of returning the updates list for rendering

### Requirement: Update timestamp labels are rendered locally
The system SHALL display adapted update publication timestamps by formatting parsed `Date` values during render.

#### Scenario: Timestamp with timezone is displayed locally
- **WHEN** the updates page renders an update with a parsed publication `Date`
- **THEN** the visible timestamp is formatted in the viewer's local timezone

#### Scenario: Timestamp label is human-friendly
- **WHEN** the updates page renders an update with a parsed publication `Date`
- **THEN** the visible timestamp uses a concise date/time label intended for human reading

#### Scenario: Parsed timestamp is missing
- **WHEN** the updates page renders an update with no parsed publication timestamp
- **THEN** the update card omits the publication timestamp without showing placeholder text

### Requirement: Timestamp display failures are visible
The system SHALL show a clear user-facing error when fetched update data cannot be adapted because a publication timestamp is invalid.

#### Scenario: Invalid timestamp blocks update display
- **WHEN** the updates fetch flow reports that a publication timestamp cannot be parsed
- **THEN** the updates page displays an error explaining that there was a problem showing the updates

#### Scenario: Invalid timestamp does not silently fall back
- **WHEN** the updates fetch flow reports that a publication timestamp cannot be parsed
- **THEN** the updates page does not display the invalid source value as if it were a valid publication time
