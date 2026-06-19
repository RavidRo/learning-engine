## ADDED Requirements

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
