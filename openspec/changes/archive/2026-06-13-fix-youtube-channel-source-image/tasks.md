## 1. Resolver Test Coverage

- [x] 1.1 Add a backend resolver test proving YouTube channel source image resolution extracts a channel-specific avatar from representative YouTube channel page metadata.
- [x] 1.2 Add a backend resolver test proving generic YouTube logo/page branding metadata returns `None` for a YouTube channel source image.
- [x] 1.3 Keep existing Spotify, feed, page, and resolver error behavior covered by the current resolver test suite.

## 2. YouTube Resolver Implementation

- [x] 2.1 Add YouTube-specific channel image extraction in the YouTube source collector adapter.
- [x] 2.2 Normalize extracted channel image URLs consistently with existing source image metadata helpers.
- [x] 2.3 Ensure the resolver preserves current invalid URL, provider unavailable, and provider miss behavior.

## 3. Verification

- [x] 3.1 Run the narrow backend resolver tests for source image resolution.
- [x] 3.2 Run the narrowest broader backend check needed to catch typing or lint regressions.
- [x] 3.3 Validate the OpenSpec change before implementation.

## 4. Browser Image Failure Handling

- [x] 4.1 Hide failed source-link images instead of leaving broken image icons visible.
- [x] 4.2 Hide failed source editor preview images instead of leaving broken image icons visible.
- [x] 4.3 Keep update thumbnail fallback state scoped to the failed URL so a later thumbnail URL can render.

## 5. YouTube Missing Channel Handling

- [x] 5.1 Treat YouTube channel page 404 responses as source image misses instead of internal server errors.
- [x] 5.2 Cover YouTube channel page 404 handling with a backend resolver test.

## 6. Optional Metadata Provider 4xx Handling

- [x] 6.1 Reproduce `/api/source-image` 500s against the running API and identify provider 4xx responses as the cause.
- [x] 6.2 Treat source image metadata provider 4xx responses as null image results for page, feed, and YouTube image resolvers.
- [x] 6.3 Cover page and feed provider 4xx handling with backend resolver tests.
