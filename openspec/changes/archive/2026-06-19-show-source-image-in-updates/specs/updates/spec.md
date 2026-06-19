## ADDED Requirements

### Requirement: Update cards show source images beside source metadata
The Updates page SHALL render a source identity image beside the source label when a visible update includes a non-empty `source_interest.source_image_url`.

#### Scenario: Source image appears beside source name
- **WHEN** the Updates page renders an update whose `source_interest.source_image_url` is non-empty
- **THEN** the update card displays that source image adjacent to the source label and source type metadata

#### Scenario: Source metadata remains visible without a source image
- **WHEN** the Updates page renders an update with no non-empty `source_interest.source_image_url`
- **THEN** the update card still displays the source label and source type without an empty image placeholder

#### Scenario: Source metadata image fails to load
- **WHEN** the Updates page renders a source metadata image and the browser reports that the image failed to load
- **THEN** the update card hides that failed image while keeping the source label and source type visible

#### Scenario: Narrow viewport displays source metadata
- **WHEN** the Updates page is viewed on a narrow viewport with source metadata images visible
- **THEN** update titles, source metadata images, source labels, timestamps, thumbnails, and save controls remain readable and do not overlap
