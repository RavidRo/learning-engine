## MODIFIED Requirements

### Requirement: Source image endpoint resolves dynamic metadata
The system SHALL provide a reusable backend endpoint that accepts a source type and source URL and returns a dynamically resolved source image URL when one can be found.

#### Scenario: Resolving a supported source image
- **WHEN** a client requests source image metadata for a supported source type and URL whose provider metadata includes an image
- **THEN** the response includes that image URL without requiring an interest id or source id

#### Scenario: No image is available
- **WHEN** a client requests source image metadata for a source whose metadata does not expose an image
- **THEN** the response succeeds with a null image URL

#### Scenario: Provider refuses optional image metadata
- **WHEN** a client requests source image metadata and the provider responds with a 4xx status while fetching optional image metadata
- **THEN** the response succeeds with a null image URL

#### Scenario: Source lookup cannot complete
- **WHEN** provider metadata cannot be fetched or parsed because of a classified resolver failure
- **THEN** the response fails with a status code and message that match the failure category

### Requirement: Source-type resolvers use provider-appropriate metadata
The system SHALL resolve source images using metadata strategies appropriate to each supported source type.

#### Scenario: YouTube channel source image
- **WHEN** source image metadata is requested for a YouTube channel source with a channel id, channel URL, or handle
- **THEN** the system attempts to resolve a channel-specific image from YouTube channel metadata

#### Scenario: YouTube generic branding is not a channel source image
- **WHEN** source image metadata is requested for a YouTube channel source and the available page metadata only exposes generic YouTube branding
- **THEN** the system returns a null image URL instead of returning the generic YouTube branding URL

#### Scenario: YouTube channel page is missing
- **WHEN** source image metadata is requested for a YouTube channel source and YouTube reports that the channel page is not found
- **THEN** the system returns a null image URL instead of failing with an internal server error

#### Scenario: Spotify podcast source image
- **WHEN** source image metadata is requested for a Spotify podcast source
- **THEN** the system attempts to resolve the podcast show image from Spotify show metadata

#### Scenario: Feed or page source image
- **WHEN** source image metadata is requested for a feed or page source
- **THEN** the system attempts to resolve a feed image, page Open Graph image, or comparable page metadata image

## ADDED Requirements

### Requirement: Source image rendering handles load failures
The webapp SHALL avoid displaying broken image icons when a resolved or manual source image URL fails to load in the browser.

#### Scenario: Interest source image fails to load
- **WHEN** the interests page displays a source image URL and the browser reports that the image failed to load
- **THEN** the interests page hides that failed image while keeping the source link visible

#### Scenario: Source editor preview image fails to load
- **WHEN** the source editor preview displays a source image URL and the browser reports that the image failed to load
- **THEN** the source editor hides that failed preview image without blocking source editing

#### Scenario: Update thumbnail image changes after a load failure
- **WHEN** an update thumbnail image URL fails to load and the update later receives a different thumbnail URL
- **THEN** the Updates page attempts to display the new thumbnail URL
