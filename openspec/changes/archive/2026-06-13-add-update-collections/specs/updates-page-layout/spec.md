## ADDED Requirements

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
