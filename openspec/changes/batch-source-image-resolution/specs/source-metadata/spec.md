## ADDED Requirements

### Requirement: Source image endpoint resolves batches of dynamic metadata
The system SHALL provide a reusable backend endpoint that accepts multiple source image lookup requests and returns one source image result per requested source id.

#### Scenario: Resolving supported source images in one request
- **WHEN** a client requests source image metadata for multiple supported sources whose provider metadata includes images
- **THEN** the response includes an image result for each requested source id without requiring interest ids

#### Scenario: Batch source image miss
- **WHEN** a batch source image request includes a source whose metadata does not expose an image
- **THEN** that source result succeeds with a null image URL while other source results remain available

#### Scenario: Batch source image lookup cannot complete
- **WHEN** a batch source image request includes a source whose provider metadata cannot be fetched or parsed because of a classified resolver failure
- **THEN** that source result includes a null image URL and diagnostic error details while other source results remain available

### Requirement: Interests page loads source images in aggregate
The interests page SHALL resolve automatic source images in aggregate so visible interest source images load within 3 seconds for normal configured interests.

#### Scenario: Visible interest sources load through a batch request
- **WHEN** the interests page displays sources without manual image URLs
- **THEN** the page requests their automatic source images through the batch source-image endpoint instead of one request per source

#### Scenario: Manual image sources are not included in automatic batch lookup
- **WHEN** a visible source has a non-empty manual `imageUrl`
- **THEN** the interests page displays the manual image and omits that source from automatic batch source-image lookup

#### Scenario: Batch automatic images are not persisted
- **WHEN** automatic source images are resolved through the batch endpoint
- **THEN** saving or reading interests still leaves those automatic image URLs out of persisted source definitions
