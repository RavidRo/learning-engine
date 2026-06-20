## ADDED Requirements

### Requirement: Interests page loads fully within the expected time
The interests page SHALL finish loading its visible content, including source images that can be resolved automatically, within 4 seconds for normal configured interests.

#### Scenario: Visible source images are included in the page load
- **WHEN** the interests page displays sources without manual image URLs and automatic source image resolution finds image URLs
- **THEN** those images appear with the visible source links before the page exceeds the 4 second loading target

#### Scenario: Manual source images do not wait for automatic resolution
- **WHEN** a visible source has a non-empty manual `imageUrl`
- **THEN** the interests page displays the manual image without delaying on automatic source image resolution

#### Scenario: Automatic image loading preserves editable source data
- **WHEN** automatic source images appear on the interests page
- **THEN** saving or reading interests still leaves those automatic image URLs out of persisted source definitions
