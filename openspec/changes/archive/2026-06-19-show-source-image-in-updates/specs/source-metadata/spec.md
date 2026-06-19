## ADDED Requirements

### Requirement: Updates page displays source identity images
The system SHALL use source image metadata included in collected updates to identify the source beside update source names on the Updates page.

#### Scenario: Update has both update image and source image
- **WHEN** a collected update includes a non-empty update-specific image URL and a non-empty `source_interest.source_image_url`
- **THEN** the Updates page renders the update-specific image as the update thumbnail and renders the source image beside the source label

#### Scenario: Update thumbnail falls back to source image while source metadata also shows it
- **WHEN** a collected update has no non-empty update-specific image URL and has a non-empty `source_interest.source_image_url`
- **THEN** the Updates page renders the source image as the update thumbnail and also renders the source image beside the source label

#### Scenario: Source image display does not persist derived metadata
- **WHEN** the Updates page displays a source image from `source_interest.source_image_url`
- **THEN** the system does not write that image URL to persisted interest source definitions
