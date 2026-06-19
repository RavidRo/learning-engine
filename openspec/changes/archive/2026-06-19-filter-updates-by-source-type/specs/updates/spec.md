## ADDED Requirements

### Requirement: Updates can be filtered by source type
The Updates page SHALL allow users to filter visible update items by source type while preserving the all-source default view.

#### Scenario: All source types are visible by default
- **WHEN** the Updates page has loaded updates from multiple source types
- **THEN** the page displays updates from every loaded source type before the user changes the source type filter

#### Scenario: User filters visible updates by source type
- **WHEN** the user selects a specific source type on the Updates page
- **THEN** the visible update groups include only updates whose `source_interest.source_type` matches the selected source type

#### Scenario: Filtered updates are grouped by interest
- **WHEN** the user filters visible updates by source type
- **THEN** the remaining visible updates continue to be grouped under their source interest names

#### Scenario: No loaded updates match the selected source type
- **WHEN** the user selects a source type with no matching loaded updates
- **THEN** the Updates page shows an empty update state for that filter instead of unrelated source type results
