## Purpose

Define update fetching, adaptation, display, layout, and update-card actions on the Updates page.

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

### Requirement: Updates summary appears above feed content
The Updates page SHALL present update summary statistics above the update feed content when updates data is available.

#### Scenario: Updates data is loaded
- **WHEN** the Updates page has an updates payload
- **THEN** the updates found, sources checked, and interests with updates statistics appear above the feed, source error callouts, update groups, and empty state content

### Requirement: Updates feed uses available panel width
The Updates page SHALL allow feed content to use the available panel width below the summary statistics.

#### Scenario: Update groups are displayed
- **WHEN** the Updates page displays grouped updates
- **THEN** the update groups are not constrained by a persistent left statistics column

### Requirement: Updates layout remains responsive
The Updates page SHALL keep summary statistics readable and non-overlapping across desktop, tablet, and mobile viewport widths.

#### Scenario: Narrow viewport displays summary statistics
- **WHEN** the Updates page is viewed on a narrow viewport
- **THEN** the summary statistics wrap or stack without overlapping header controls, feed content, or each other

### Requirement: Updates behavior is unchanged
The Updates page SHALL preserve existing update refresh, filtering window, error callout, empty state, and grouping behavior.

#### Scenario: User refreshes updates
- **WHEN** the user changes the update window or refreshes updates
- **THEN** the page uses the same update collection behavior and displays the same categories of results and errors as before the layout change

### Requirement: Updates can be saved from the Updates page
The Updates page SHALL provide save-to-collection actions for each visible update without changing existing update refresh, filtering, grouping, error, or empty-state behavior.

#### Scenario: User saves a visible update to a fixed collection
- **WHEN** the Updates page displays an update and the user chooses a fixed collection save action for it
- **THEN** the page sends the update snapshot to the collection save API and gives feedback using the existing toast behavior

#### Scenario: User refreshes updates after collection actions are added
- **WHEN** the user changes the update window or refreshes updates
- **THEN** the page keeps using the existing update collection behavior and displays the same categories of results and errors as before collection actions were added

#### Scenario: Updates page displays on a narrow viewport
- **WHEN** the Updates page is viewed on a narrow viewport with save-to-collection controls visible
- **THEN** update titles, metadata, thumbnails, and save controls remain readable and do not overlap

### Requirement: Update descriptions are displayed
The Updates page SHALL display an update description under the update title when the fetched update includes a non-blank summary.

#### Scenario: Update summary is visible below title
- **WHEN** the Updates page renders an update with a non-blank `summary`
- **THEN** the update card displays that summary directly below the update title and above the source metadata

#### Scenario: Missing summary does not show placeholder text
- **WHEN** the Updates page renders an update without a `summary`
- **THEN** the update card omits the description line without showing placeholder text

#### Scenario: Blank summary does not reserve description space
- **WHEN** the Updates page renders an update with a whitespace-only `summary`
- **THEN** the update card omits the description line without reserving empty description space

#### Scenario: Existing update card behavior is preserved
- **WHEN** the Updates page renders an update description
- **THEN** the update card still displays its title, source metadata, optional publication timestamp, thumbnail, and save-to-collection controls according to the existing behavior

### Requirement: Updates page loads within the target performance budget
The Updates page SHALL fully load the updates view in under 4 seconds when enabled upstream sources respond within the target budget.

#### Scenario: Updates load completes under four seconds
- **WHEN** the user opens the Updates page and the enabled source endpoints respond within the target budget
- **THEN** the page displays the loaded updates view in under 4 seconds

#### Scenario: Source documents are not fetched redundantly
- **WHEN** update collection and source image enrichment need the same feed or page source document during an updates load
- **THEN** the system reuses the successful source document response instead of issuing a second equivalent network fetch

#### Scenario: Failed source responses remain retryable
- **WHEN** a source document fetch fails during an updates load
- **THEN** the failed response is not cached and a later updates load can retry that source
