## Why

Linear ticket RAV-27 reports that YouTube channel sources display the generic YouTube logo instead of the channel's own image. This makes source previews and update thumbnails less useful because multiple YouTube sources become visually indistinguishable.

## What Changes

- Tighten YouTube channel source image resolution so it prefers channel-specific avatar metadata from the YouTube channel page.
- Prevent the resolver from accepting generic YouTube branding as a successful channel source image.
- Keep the existing `/api/source-image` contract, source editor behavior, update collection behavior, and persistence rules unchanged.
- Add backend resolver tests that cover channel-specific image extraction and generic-logo rejection.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `source-image-resolution`: YouTube channel source image resolution must return a channel-specific image when provider metadata exposes one and must not return generic YouTube branding as the source image.

## Impact

- Backend YouTube source image resolver in `backend/learning_engine/infrastructure/source_collectors/youtube.py`.
- Shared image metadata parsing helpers only if the YouTube resolver needs a reusable parsing primitive.
- Backend resolver tests in `backend/tests/infrastructure/source_images/test_resolver.py`.
- No public API, datastore, dependency, deployment, or frontend contract changes.
