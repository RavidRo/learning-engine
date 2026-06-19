## Why

RAV-13 asks for a built-in collection that records updates the user has checked out by clicking them. Today, collected updates can be saved manually to `See Later` and `Liked`, but there is no automatic history trail for opened updates.

## What Changes

- Add `History` as a protected fixed collection with stable id `history`.
- Automatically save an update snapshot to `History` when the user clicks a visible update link on the Updates page.
- Keep the existing collection persistence, deterministic update key, idempotent save behavior, ordering, and Collections page rendering.
- Hide `History` from the explicit save-to-collection buttons so history membership is driven by checkout clicks, not manual toggles.

## Assumptions

- `History` is a protected built-in collection similar to the existing fixed collections.
- "Checked out" means clicking the update title link that opens the update URL.
- Re-clicking the same update should be idempotent and preserve the first history timestamp, matching existing collection semantics.

## Architectural Trade-off

This is both a persistence and frontend behavior change. The implementation reuses the existing fixed-collection domain model, `CollectionRepository`, SQLModel-backed store, and `/api/collections/{collection_id}/updates` API instead of adding a dedicated history table or endpoint. That keeps History under the same validation, snapshot preservation, and idempotency rules as the other built-ins. The trade-off is that History appears in the general collections list and can be removed through the existing Collections page controls, but the feature avoids duplicating collection persistence logic or creating a second durable update concept.

## Impact

- Specs: `collections`
- Backend: fixed collection ids and storage seeding behavior.
- Webapp: collection schema, Updates page click handling, and collection action filtering.
