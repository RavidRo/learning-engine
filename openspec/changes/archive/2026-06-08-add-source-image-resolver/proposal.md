## Why

Source images are currently only available when a user manually enters an `imageUrl`. Many source types already carry canonical artwork, such as YouTube channel avatars and Spotify podcast images, so the app can make source cards and update avatars more useful without asking users to maintain image URLs by hand.

## What Changes

- Add a reusable API endpoint that resolves an image URL for a source from its `type` and `url`.
- Keep automatically resolved images dynamic and derived; do not persist them into `backend/data/interests.json`.
- Preserve the existing manual `imageUrl` behavior as an explicit user override.
- Use source-type-specific lookup strategies for supported source types, beginning with YouTube channels and Spotify podcasts, and add best-effort metadata lookup for web feed/page sources.
- Allow image resolution failures to fall back quietly instead of failing interest saving or update collection.

## Capabilities

### New Capabilities

- `source-image-resolution`: Resolves dynamic source image metadata from source definitions while preserving user-provided image overrides.

### Modified Capabilities

None.

## Impact

- Backend API: add a source image resolution endpoint and response model.
- Backend source adapters: add reusable image metadata resolution helpers by source type.
- Update collection: optionally attach dynamic source images when a source has no manual image URL.
- Webapp API/client state: call the resolver endpoint where source previews or update avatars need derived images.
- Tests: cover endpoint behavior, manual override precedence, non-persistence, and per-type resolver fallbacks.
