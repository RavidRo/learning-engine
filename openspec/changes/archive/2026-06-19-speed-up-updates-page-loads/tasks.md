## 1. Fetch Cache Coverage

- [x] 1.1 Add backend tests for a cached fetcher that reuses successful `fetch_url` responses for identical URL/header requests.
- [x] 1.2 Add backend tests proving byte responses, JSON responses, and requests with different headers do not share cache entries.
- [x] 1.3 Add backend tests proving failed fetches are not cached and are retried on the next equivalent request.

## 2. Backend Implementation

- [x] 2.1 Implement a bounded TTL cached fetcher wrapper in the infrastructure fetching layer.
- [x] 2.2 Wire the cached fetcher into FastAPI app startup so source update collection and source image resolution share successful source-document responses.
- [x] 2.3 Keep source-update response caching behavior unchanged for five-minute reuse, selected-days separation, expiry, and retry-on-error.

## 3. Updates Performance Verification

- [x] 3.1 Add an updates API test proving feed/page update collection and source image enrichment do not issue duplicate equivalent source-document fetches.
- [x] 3.2 Add a deterministic performance-budget test or timing guard showing the updates load path completes under 4 seconds when upstream source responses stay within the target budget.
- [x] 3.3 Run the focused backend tests for update collection/fetching and then `task check` when feasible.
