## Why

Updates can carry their own artwork, such as RSS item thumbnails or media images. The Updates page currently renders the source image for every update, which hides more specific update artwork when it is available.

## What Changes

- Capture an optional image URL on individual collected updates.
- Parse update-specific images from feed item metadata where available.
- Render update thumbnails using the priority: update image, user-provided source image, then automatically resolved source image.
- Preserve existing fallback initials when no image is available or an image fails to load.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `source-image-resolution`: adds update-specific thumbnail precedence over manual and automatic source images.

## Impact

- Backend domain/update payload: add optional `image_url` on collected updates.
- Backend feed adapter: extract item-level media/enclosure image metadata.
- Webapp update feed: choose thumbnails from update image before source image.
- Tests: cover update image parsing and thumbnail precedence.
