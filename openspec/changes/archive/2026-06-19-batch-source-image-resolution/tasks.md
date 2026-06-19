## 1. Backend API

- [x] 1.1 Add batch source image request/response schemas keyed by source id.
- [x] 1.2 Add `POST /api/source-images` that resolves requested source images concurrently through the existing provider boundary and returns per-source diagnostics.
- [x] 1.3 Add presentation tests for successful batch resolution, per-source misses/errors, and non-persistence of automatic images.

## 2. Webapp Loading

- [x] 2.1 Add a batch source image client and response schema.
- [x] 2.2 Update source-link image loading to use one batch query for visible automatic source images while preserving manual image precedence.

## 3. Verification

- [x] 3.1 Run narrow backend tests for source image routes.
- [x] 3.2 Run relevant webapp checks and `task check` if feasible.
