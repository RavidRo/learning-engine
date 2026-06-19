## Context

The interests page currently renders source links per interest. Each source without a manual `imageUrl` starts its own `POST /api/source-image` request through React Query. For users with many interests and sources, that creates a long tail of browser requests and repeated backend routing overhead before all source images are visible.

Source images are derived metadata. Existing requirements state they must not be persisted into interest definitions, and source image resolution already flows through the backend `SourceImageProvider` port.

## Goals / Non-Goals

**Goals:**

- Load all visible interest source images within 3 seconds for normal configured interests.
- Keep automatic source images derived and non-persistent.
- Preserve manual source image precedence.
- Reuse the existing source-image provider boundary and resolver error classification.

**Non-Goals:**

- Add a durable image cache or new datastore.
- Change source editor preview behavior.
- Change resolver provider logic for YouTube, Spotify, feed, page, or Twitter sources.

## Decisions

1. Add `POST /api/source-images` for batch source-image resolution.
   - The endpoint accepts source entries with `id`, `type`, and `url`, then returns `images` entries keyed by `id`.
   - Rationale: a batch endpoint reduces client/server round trips and lets the backend resolve independent sources concurrently while keeping the single-source endpoint stable for existing callers.
   - Alternative considered: make the frontend issue all single-source queries earlier. Rejected because it still creates one HTTP request per source and keeps the same long-tail network pattern.

2. Resolve batch entries concurrently through the existing `SourceImageProvider` boundary.
   - Rationale: the provider boundary already owns source-type dispatch and external fetch behavior. Concurrency belongs in the presentation/use-case orchestration for the batch request, not inside individual provider adapters.
   - Alternative considered: add a provider-level batch protocol. Rejected for this ticket because current providers resolve independent URLs and no provider-specific bulk API exists.

3. Return per-source batch results instead of failing the whole batch for classified resolver failures.
   - Rationale: one broken or misconfigured source should not prevent other images from loading. Errors remain observable in the response entry for that source.
   - Alternative considered: fail the whole request on the first resolver error. Rejected because it would preserve a slow and brittle all-or-nothing user experience.

4. Do not add a durable cache for RAV-26.
   - Rationale: a cache would be a persistence/cross-cutting change with invalidation, storage, and deployment concerns. Batch concurrency is smaller, keeps derived metadata derived, and directly addresses one-by-one loading.
   - Alternative considered: persist resolved source images on interests. Rejected because existing source-metadata requirements explicitly forbid persisting automatic images.

## Risks / Trade-offs

- Public API surface grows with a second endpoint -> Mitigated by keeping the existing endpoint unchanged and using the new endpoint only for aggregate page loading.
- Per-entry errors could be ignored by the UI -> Mitigated by returning `imageUrl: null` for those entries so source links still render, and by retaining status/detail data for diagnostics.
- Backend concurrency can increase outbound provider requests -> Mitigated by only batching visible sources needing automatic image lookup and preserving manual-image short-circuiting in the frontend.
- The 3-second DOD depends on external provider responsiveness -> Mitigated by removing one-by-one browser request overhead; provider-level timeouts remain governed by the existing fetcher behavior.
