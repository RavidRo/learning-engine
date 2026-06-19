## Why

RAV-29 asks for the Updates page to show the source image near the source name, in addition to the update image already shown as the update thumbnail. Today a collected update with update-specific artwork can hide the source identity image because the thumbnail slot prefers `update.image_url`.

## What Changes

- Render a small source image beside the source label in each Updates page update card when `source_interest.source_image_url` is available.
- Keep the existing large update thumbnail behavior unchanged: update-specific image first, then source image, then source initial fallback.
- Hide the small source image if its URL is missing or fails to load, leaving the source label and source type readable.
- Preserve update grouping, refresh, save-to-collection actions, and responsive layout behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `updates`: Update cards show source identity imagery next to source metadata without replacing update thumbnails.
- `source-metadata`: Source images continue to supply update thumbnails as a fallback and also appear as source identity metadata when available.

## Impact

- Affected code is expected to be limited to the webapp Updates page components/styles and focused frontend verification.
- No backend API, persistence, datastore, security, or integration changes are planned.
- Architectural trade-off: reuse the existing `source_interest.source_image_url` field from update collection rather than adding a new endpoint or persisted source-image field. This keeps derived source metadata transient and follows the established source metadata boundary, at the cost of only showing source images that are already present in collected update payloads.
