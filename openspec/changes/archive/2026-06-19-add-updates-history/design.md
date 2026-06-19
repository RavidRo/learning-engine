## Context

The app already has fixed collections backed by SQLModel persistence. Collection saves store update snapshots with deterministic keys, and repeated saves return the existing row without changing `saved_at`.

## Decisions

1. Add `history` to the backend fixed collection registry.

   The backend remains authoritative for valid collection ids and display names. Existing `ensure_data_store()` seeding creates missing fixed rows idempotently, so existing databases gain the `History` row when the service starts.

2. Save history through the existing collection save API.

   The frontend will call `saveUpdateToCollection("history", update)` when the update title link is clicked. The click is not blocked by the save request; opening the update remains the primary action.

3. Keep History out of manual Updates-page collection buttons.

   Existing save controls are explicit user curation actions. History is automatic checkout state, so the button list filters out `history` while the Collections page still displays all collections returned by the API.

## Risks

- If the history save request fails while the browser opens the external URL, the user may not notice. This follows current toast/error behavior for collection mutations; no fallback queue is introduced.
- Existing databases rely on startup seeding to add the new fixed row. This matches the current fixed-collection pattern and avoids a separate migration path for a single seeded row.
