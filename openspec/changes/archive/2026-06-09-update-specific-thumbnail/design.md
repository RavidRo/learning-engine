## Context

Source thumbnails are already carried in `source_interest.source_image_url`, with manual `imageUrl` taking precedence over automatically resolved source metadata. The missing layer is artwork attached to a specific update.

## Decision

Add `image_url` to the existing update domain model rather than creating a separate presentation DTO. Feed item parsing will populate it from item-level image metadata. The frontend will keep source image behavior intact by using the update image only as the first candidate before falling back to `source_interest.source_image_url`.

## Details

1. `SourceUpdate` accepts an optional `image_url` value.
2. Feed parsing extracts the first suitable image URL from item metadata in this order:
   - Media RSS thumbnail URLs.
   - Media RSS content entries whose medium or MIME type is image-like.
   - RSS enclosure links whose MIME type is image-like.
3. Relative and protocol-relative item image URLs are normalized against the update URL when available.
4. The Updates page renders a thumbnail candidate selected as:
   - `update.image_url` when non-empty.
   - `update.source_interest.source_image_url` when non-empty.
   - Existing source-label fallback initial.

## Risks / Trade-offs

- Feed media metadata varies by publisher, so extraction remains best-effort and limited to common feedparser-normalized fields.
- Adding `image_url` to the domain update model extends the API payload shape, but it is optional and preserves compatibility for existing updates.
