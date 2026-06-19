## Context

The Updates page loads by enabling a React Query request to `/api/updates?days=N`. The backend reads enabled interests, concurrently collects updates for each enabled source, enriches updates with source metadata, and returns a single aggregate response before the page can finish loading.

The current backend already caches collected source updates for five minutes, but an uncached load can fetch the same feed/page source URL twice: once for updates and again for source image metadata. The local configured interests currently include many feed/page sources without manual `imageUrl` values, so duplicate source-document fetches directly affect first-load latency.

## Goals / Non-Goals

**Goals:**

- Make the Updates page fully load in under 4 seconds when upstream sources respond within the target budget.
- Eliminate duplicate successful source-document HTTP fetches during a single update load and across the existing short cache window.
- Keep the existing `/api/updates` response shape and visible Updates page behavior.
- Preserve retry behavior for source failures.

**Non-Goals:**

- Do not add streaming updates, background jobs, polling, or a new datastore.
- Do not remove source image enrichment from update responses.
- Do not promise a 4-second load when a third-party source itself exceeds the budget or times out.

## Decisions

- Add a bounded successful-GET cache at the HTTP fetcher boundary. This lets update collectors and source image resolvers share the same source document bytes without changing collector interfaces or response models.
- Cache keys include response kind, URL, and request headers. This prevents byte and JSON fetches or provider-specific authenticated requests from colliding.
- Cache only successful responses. Exceptions, non-2xx responses, and parsing failures remain uncached so existing source-error retry behavior is preserved.
- Align the fetch cache TTL with the existing five-minute source update cache. This keeps freshness expectations simple and avoids introducing a second public freshness policy.
- Keep the frontend unchanged unless measurement shows avoidable client-side blocking. The observed bottleneck is backend aggregate response time, not rendering or browser request fan-out.

## Risks / Trade-offs

- Cached source bytes may be up to five minutes stale -> Mitigated by matching the current source update cache TTL.
- Memory use increases with cached response bodies -> Mitigated with a bounded cache size and existing process-local cache pattern.
- The 4-second target depends on upstream responsiveness -> Mitigated by documenting that slow or timed-out third-party sources can still exceed the budget and by removing duplicate app-controlled fetch work.
