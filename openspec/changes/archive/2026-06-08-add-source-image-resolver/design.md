## Context

Sources already support an optional manual `imageUrl` and collected updates already carry `source_interest.source_image_url` to the webapp. Today that value is only user-authored data from `backend/data/interests.json`; the backend does not derive source artwork from YouTube, Spotify, feed, or page metadata.

The change introduces dynamic image resolution as source metadata. The resolver must be reusable by the webapp and update collection, while keeping persisted interests focused on user configuration rather than cached external metadata.

## Goals / Non-Goals

**Goals:**

- Provide one backend endpoint that resolves a source image from `{ type, url }`.
- Reuse the same resolver internally when collected updates need an avatar and no manual `imageUrl` exists.
- Preserve manual `imageUrl` as the highest-priority source image.
- Keep automatic images out of `interests.json`.
- Let the source image resolver classify failures while each consumer decides how to handle them.
- Treat failed image lookup as absence of metadata during update collection, not as an update collection failure.
- Preview dynamic images in the source editor automatically after debounced URL input.
- Log source image resolver fallbacks so provider misses and internal resolver errors remain diagnosable.

**Non-Goals:**

- Download, proxy, transform, resize, or store image binaries.
- Introduce a persistent metadata cache or database table.
- Guarantee that every source has an image.
- Replace the existing manual image URL field.

## Decisions

1. Add a dedicated resolver module instead of embedding image lookup in the collector.

   The collector should keep orchestrating update collection. A separate source metadata/image resolver keeps adapter parsing concerns close to source-type logic and lets both API routes and collection code share one path.

   Alternative considered: resolve images only in the webapp. That would duplicate source-type parsing rules in TypeScript and require browser calls to third-party origins, which is brittle and uneven across providers.

2. Add a reusable API endpoint for dynamic images.

   The endpoint accepts source type and URL and returns a nullable image URL. It does not require an interest id or source id because the image is derived from source data, not persisted source state.

   Alternative considered: enrich `/api/interests` responses. That would make a read of local configuration perform network work and blur persisted data with derived metadata.

3. Do not persist automatically resolved image URLs.

   `interests.json` remains the user's source configuration. Automatic images can change as providers update their branding, so they should be resolved dynamically and cached only in memory if needed for performance.

   Alternative considered: write resolved images back during save. That creates slow/flaky saves and makes external metadata look user-authored.

4. Manual image URL wins.

   When a source has a non-empty `imageUrl`, update collection and UI preview use it directly. The resolver endpoint can still resolve source metadata for preview workflows, but automatic values must not overwrite manual values unless the user explicitly edits the field.

5. Source editor preview is automatic and debounced.

   The editor should request image metadata after the source URL settles instead of requiring a user-controlled lookup button. A debounce keeps typing from sending a request for every keystroke. Once the resolver responds, the control should show either the image preview or an explicit "no image found" style message, with no repeat lookup button.

   Alternative considered: keep an explicit preview button. That avoids background requests, but it adds an unnecessary decision point and leaves users confused when no result appears.

6. Resolver failures are handled by consumers.

   Provider errors, parse misses, unsupported metadata, or invalid external responses should be converted into an explicit `SourceImageProviderError` subclass at the exact source adapter boundary where the cause is known. Missing local/source configuration should use a configuration-specific subclass. Provider downtime should use a provider-unavailable subclass only for provider 5xx HTTP responses. Provider 4xx responses and broad exception classes such as `OSError`, `TypeError`, and `ValueError` should not be labeled provider errors unless that specific raise site has been intentionally adapted. The resolver should raise these classified errors instead of deciding fallback behavior for all callers. Update collection should log known provider-side failures at info level, log unexpected internal resolver exceptions at error level with exception details, and continue to use the current fallback avatar behavior. The `/api/source-image` endpoint should return a status-coded error response that matches the classified failure.

7. Source previews are not circular avatars.

   Source metadata images vary widely, including logos and banners. The editor preview should not force a circular crop; the update feed can keep its existing avatar treatment separately.

8. Source-type adapters own their metadata strategy.

   YouTube should reuse channel URL normalization and inspect channel page/feed metadata for a channel image. Spotify should use the existing show id parser and request show metadata. Feed/page sources should parse feed-level image/logo or page metadata such as `og:image`; page-relative image URLs should resolve against the source URL.

## Risks / Trade-offs

- Third-party markup changes can break image extraction -> Keep extraction best-effort and covered by focused parser tests.
- Resolver calls can add network latency -> Use the existing `HttpFetcher` and consider a small in-memory TTL cache if repeated calls become noticeable.
- Automatic editor lookup can fire while users type -> Debounce URL changes before requesting metadata.
- Some image URLs may be relative or protocol-relative -> Normalize resolved URLs using the source or page URL as base.
- Returning `null` can look like failure to users -> Return `null` only for successful lookups with no available image and show an explicit no-image state in the editor.
- Spotify and Twitter/X metadata may require provider tokens -> Surface configuration failures from the preview endpoint while update collection logs and continues without an automatic image.
