## Purpose

Define how source image metadata is dynamically resolved, previewed, used during update collection, and kept separate from persisted interest configuration.

## Requirements

### Requirement: Source image endpoint resolves dynamic metadata
The system SHALL provide a reusable backend endpoint that accepts a source type and source URL and returns a dynamically resolved source image URL when one can be found.

#### Scenario: Resolving a supported source image
- **WHEN** a client requests source image metadata for a supported source type and URL whose provider metadata includes an image
- **THEN** the response includes that image URL without requiring an interest id or source id

#### Scenario: No image is available
- **WHEN** a client requests source image metadata for a source whose metadata does not expose an image
- **THEN** the response succeeds with a null image URL

#### Scenario: Source lookup cannot complete
- **WHEN** provider metadata cannot be fetched or parsed because of a classified resolver failure
- **THEN** the response fails with a status code and message that match the failure category

### Requirement: Automatic source images are not persisted
The system MUST treat automatically resolved source images as derived metadata and MUST NOT write them to persisted interest source definitions.

#### Scenario: Saving interests after resolving an image
- **WHEN** a source image has been resolved dynamically for a source whose persisted `imageUrl` is null
- **THEN** saving interests leaves that source `imageUrl` null in persisted interest data

#### Scenario: Reading interests after resolving an image
- **WHEN** a client reads interests after source image metadata has been resolved
- **THEN** the interests response contains only the persisted source image values and does not include automatic image URLs as source `imageUrl` values

### Requirement: Manual source images take precedence
The system SHALL preserve user-provided source image URLs as explicit overrides over automatically resolved source images.

#### Scenario: Update collection uses manual image first
- **WHEN** an enabled source has a non-empty manual `imageUrl`
- **THEN** collected updates for that source use the manual image URL without replacing it with an automatically resolved image

#### Scenario: Update collection falls back to automatic image
- **WHEN** an enabled source has no manual `imageUrl` and the resolver finds an image
- **THEN** collected updates for that source include the resolved image URL in `source_interest.source_image_url`

#### Scenario: Update collection has no source image
- **WHEN** an enabled source has no manual `imageUrl` and no automatic image can be resolved
- **THEN** collected updates for that source include a null `source_interest.source_image_url`

#### Scenario: Update collection source image lookup fails
- **WHEN** an enabled source has no manual `imageUrl` and automatic image lookup raises a resolver error
- **THEN** update collection logs the failure and collected updates for that source include a null `source_interest.source_image_url`

#### Scenario: Update thumbnail uses update image before source image
- **WHEN** a collected update includes a non-empty update-specific image URL and its source also has a manual or automatically resolved image URL
- **THEN** the Updates page renders the update-specific image as the update thumbnail

#### Scenario: Update thumbnail falls back to source image
- **WHEN** a collected update has no non-empty update-specific image URL and its source has a manual or automatically resolved image URL
- **THEN** the Updates page renders the source image as the update thumbnail

#### Scenario: Update thumbnail falls back to source initial
- **WHEN** a collected update has no non-empty update-specific image URL and no source image URL
- **THEN** the Updates page renders the existing source-label fallback initial

### Requirement: Source-type resolvers use provider-appropriate metadata
The system SHALL resolve source images using metadata strategies appropriate to each supported source type.

#### Scenario: YouTube channel source image
- **WHEN** source image metadata is requested for a YouTube channel source with a channel id, channel URL, or handle
- **THEN** the system attempts to resolve the channel image from YouTube channel metadata

#### Scenario: Spotify podcast source image
- **WHEN** source image metadata is requested for a Spotify podcast source
- **THEN** the system attempts to resolve the podcast show image from Spotify show metadata

#### Scenario: Feed or page source image
- **WHEN** source image metadata is requested for a feed or page source
- **THEN** the system attempts to resolve a feed image, page Open Graph image, or comparable page metadata image

### Requirement: Source editor previews automatic images
The source editor SHALL preview dynamic source images automatically after a source URL is entered, without persisting the resolved image URL into the source definition.

#### Scenario: Preview is fetched after URL entry
- **WHEN** a user enters or changes a source URL and the source has no manual `imageUrl`
- **THEN** the editor waits for a debounce interval before requesting source image metadata

#### Scenario: Preview image is found
- **WHEN** debounced source image metadata resolves to an image URL
- **THEN** the editor displays the preview image and no repeated lookup action is shown

#### Scenario: Preview image is not found
- **WHEN** debounced source image metadata resolves with a null image URL
- **THEN** the editor displays a clear message that no image was found

#### Scenario: Manual image preview
- **WHEN** a source has a non-empty manual `imageUrl`
- **THEN** the editor previews the manual image without requesting automatic source image metadata

#### Scenario: Preview image shape
- **WHEN** a source image preview is displayed
- **THEN** the image is not cropped into a circular avatar

### Requirement: Interests page displays source images

The interests page SHALL display source images near each visible source link when either a manual source image or a dynamically resolved source image is available.

#### Scenario: Manual image appears beside a source

- **WHEN** an interest source has a non-empty manual `imageUrl`
- **THEN** the interests page displays that image beside the source label

#### Scenario: Automatic image appears beside a source

- **WHEN** an interest source has no manual `imageUrl` and dynamic source image resolution returns an image URL
- **THEN** the interests page displays the resolved image beside the source label without persisting it into the source definition

#### Scenario: No image is available beside a source

- **WHEN** an interest source has no manual `imageUrl` and dynamic source image resolution does not return an image URL
- **THEN** the interests page keeps the source link visible without an image
