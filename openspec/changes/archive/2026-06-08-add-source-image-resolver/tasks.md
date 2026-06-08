## 1. Backend Contract

- [x] 1.1 Add request and response models for source image resolution.
- [x] 1.2 Add a backend source image resolver module with a public async function that accepts source type, URL, and fetch dependencies.
- [x] 1.3 Add a reusable API endpoint that returns a nullable resolved image URL without reading or writing persisted interests.

## 2. Source-Type Resolution

- [x] 2.1 Implement YouTube channel image resolution using existing channel URL normalization and channel metadata parsing.
- [x] 2.2 Implement Spotify podcast image resolution using existing show id parsing and Spotify show metadata.
- [x] 2.3 Implement feed/page image resolution from feed-level image data, Open Graph image metadata, or comparable page metadata.
- [x] 2.4 Normalize relative and protocol-relative image URLs against the source metadata URL.
- [x] 2.5 Treat provider errors, missing credentials, and parse misses as null image results.
- [x] 2.6 Log known provider-side image resolution misses at info level and unexpected internal resolver exceptions at error level.
- [x] 2.7 Convert known provider boundary failures into `SourceImageProviderError` and route all other exceptions through one logged internal-error handler.
- [x] 2.8 Avoid broad request-wrapper exception conversion; only adapt exceptions at raise sites with known provider semantics.
- [x] 2.9 Split source image provider errors into missing configuration and provider 5xx downtime, while treating 4xx responses as unexpected.
- [x] 2.10 Raise classified resolver failures and let each consumer choose its handling behavior.

## 3. Update Collection Integration

- [x] 3.1 Resolve source images during update collection only when the source has no non-empty manual `imageUrl`.
- [x] 3.2 Attach resolved automatic images to `source_interest.source_image_url` without mutating source definitions.
- [x] 3.3 Preserve current fallback behavior when no automatic image is available.
- [x] 3.4 Log source image resolver failures during update collection and continue without an automatic image.

## 4. Webapp Integration

- [x] 4.1 Add client API and schema support for source image resolution responses.
- [x] 4.2 Use the resolver endpoint for source image preview/autofill workflows without automatically persisting derived image URLs.
- [x] 4.3 Keep update avatar rendering compatible with manual, automatic, and missing source image URLs.
- [x] 4.4 Replace the manual preview lookup action with automatic debounced source image preview.
- [x] 4.5 Show explicit loading, no-image-found, and unavailable states for source image previews.
- [x] 4.6 Render editor preview images without circular cropping.

## 5. Verification

- [x] 5.1 Add backend tests for endpoint success, null fallback, and non-persistence.
- [x] 5.1.1 Add backend tests for endpoint error responses from classified resolver failures.
- [x] 5.2 Add backend tests for manual image precedence and automatic image fallback during update collection.
- [x] 5.3 Add focused resolver tests for YouTube, Spotify, and feed/page metadata parsing.
- [x] 5.4 Add webapp tests or type-check coverage for resolver response handling.
- [x] 5.5 Add resolver logging coverage for provider misses and internal errors.
- [x] 5.6 Run `task check`.
