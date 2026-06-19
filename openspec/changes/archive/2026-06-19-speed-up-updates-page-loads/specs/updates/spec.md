## ADDED Requirements

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
