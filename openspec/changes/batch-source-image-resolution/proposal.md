## Why

RAV-26 reports that loading source images for all interests is too slow because each source image is fetched one by one. The interests page should load visible interest source images within 3 seconds for normal configured sources without persisting derived image URLs.

## What Changes

- Add a batch source-image API that accepts multiple source descriptors and returns image URLs keyed by source id.
- Update the interests page to resolve automatic source images through the batch API per visible source set instead of issuing one request per source link.
- Keep manual source image URLs as immediate overrides and keep derived automatic image URLs out of persisted interest data.
- Preserve the existing single-source image endpoint for editor previews and compatibility.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `source-metadata`: add batch resolution behavior and the aggregate interests-page performance requirement for source images.

## Impact

- Public API: adds `POST /api/source-images` while keeping `POST /api/source-image` unchanged.
- Backend presentation/application: validates batch payloads and resolves source images concurrently through the existing `SourceImageProvider` boundary.
- Webapp: source-link image loading switches from many individual React Query calls to one batch query per rendered interest source set.
- Tests: add backend route coverage and frontend/build verification where feasible.
