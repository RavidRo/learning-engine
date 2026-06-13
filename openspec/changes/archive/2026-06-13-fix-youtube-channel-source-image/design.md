## Context

Source image resolution is a backend boundary used by the `/api/source-image` endpoint, source editor previews, and update collection enrichment. For YouTube channel sources, `resolve_youtube_image` currently fetches the channel page and passes the whole document through the shared generic HTML metadata parser. That parser accepts common page image markers such as Open Graph image tags and icon links, which is appropriate for generic pages but can accept provider branding on YouTube channel pages.

RAV-27 narrows the YouTube resolver requirement: a YouTube channel source image should be the channel image, not the generic YouTube logo. The existing source image API contract, persistence behavior, and frontend rendering behavior remain unchanged.

## Goals / Non-Goals

**Goals:**

- Resolve YouTube channel source images from channel-specific metadata on the YouTube channel page.
- Reject generic YouTube branding as a successful YouTube channel image result.
- Preserve existing resolver error classification and null-on-provider-miss behavior.
- Cover the behavior with focused backend resolver tests.

**Non-Goals:**

- Add a YouTube Data API dependency or require YouTube credentials.
- Persist automatically resolved YouTube channel images.
- Change source editor, interests page, updates page, or `/api/source-image` response shape.
- Implement image proxying, caching, downloading, or validation beyond URL selection.

## Decisions

1. Keep the fix inside the YouTube source collector adapter.

   The existing architecture separates orchestration, provider adapters, and generic metadata helpers. The incorrect behavior is provider-specific: generic HTML image metadata is too broad for YouTube channel pages. Keeping the selection in `youtube.py` avoids making `html_image_url` aware of YouTube branding rules that do not apply to normal pages.

   Alternative considered: change `html_image_url` to globally reject YouTube logo URLs. That would create a provider-specific rule inside a shared helper and could break legitimate pages that use YouTube-hosted images.

2. Prefer channel-specific metadata before generic page metadata.

   The implementation should parse YouTube channel page data for channel avatar URLs, such as structured initial-data fields or image objects associated with the channel header/avatar. If no channel-specific image can be identified, the resolver should return `None` rather than accepting generic page icons.

   Alternative considered: keep Open Graph parsing and add a denylist for obvious logo URLs. A denylist alone would still treat generic page metadata as authoritative and may miss future branding URLs.

3. Preserve the existing fetch and error boundary.

   The resolver will continue to fetch the normalized channel page through `fetch_provider_bytes(page_url, fetch, "YouTube")`. Provider 5xx errors remain classified as provider unavailable, invalid source URLs remain configuration errors, and parser misses return `None`.

   Alternative considered: resolve the channel feed first and look for feed-level author artwork. YouTube Atom feeds do not consistently provide channel avatar metadata, and the existing source image resolver already operates against channel pages.

## Risks / Trade-offs

- YouTube page markup changes -> Mitigation: keep parsing focused on stable serialized image URL structures and test representative markup patterns.
- Some channels expose only generic page metadata -> Mitigation: return `None` for a provider miss instead of showing misleading generic branding.
- Avatar image URLs may include escaped JSON or relative forms -> Mitigation: normalize extracted URLs through existing image URL normalization behavior where applicable.
