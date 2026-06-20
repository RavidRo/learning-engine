## ADDED Requirements

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
