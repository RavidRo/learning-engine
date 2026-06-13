## Context

RAV-14 adds Collections to Learning Engine. Updates are currently collected on demand through `/api/updates`, grouped in the React Updates page, and not persisted as first-class records. The backend already uses clean architecture boundaries: domain models in `domain/`, ports and use cases in `application/`, SQLModel persistence in `infrastructure/storage.py`, and FastAPI routes in `presentation/`.

Collections are a persistence and public API change. The user decision during ticket grilling was to save a snapshot of the update plus a deterministic update key. That avoids depending on future source collection results to rediscover a saved update.

## Goals / Non-Goals

**Goals:**

- Persist the two fixed collections, `See Later` and `Liked`.
- Let the user save any visible update snapshot into either fixed collection from the Updates page.
- Preserve the timestamp when the update was saved to a collection.
- List collections and their saved updates ordered by `saved_at` descending.
- Let the user remove an update from a collection.
- Keep the existing Updates page collection, filtering, grouping, error, and empty-state behavior intact.

**Non-Goals:**

- Creating, deleting, renaming, or reordering collections.
- Sharing collections between users or exporting/importing collections.
- Recollecting sources to refresh saved update snapshots.
- Introducing a second datastore or a background job.
- Backfilling collections from existing updates, because updates are not currently stored.

## Decisions

1. Add collection models to the domain and a collection repository port.

   Collection concepts should live in `learning_engine/domain/collections.py`, with application use cases depending on a `CollectionRepository` protocol in `application/ports.py`. Presentation will call application use cases rather than talking to infrastructure directly. This follows the current architecture and keeps collection persistence replaceable.

   Alternative considered: add collection helper methods directly to FastAPI routes. Rejected because it bypasses the established application boundary for a persistent feature.

2. Extend the existing SQLModel store instead of adding another datastore.

   Add collection tables to the current SQLModel metadata and implement `CollectionRepository` on the existing store. `ensure_data_store()` should create the new tables and seed the fixed collection rows idempotently. This keeps interests and collections in the same configured database and avoids a separate lifecycle.

   Alternative considered: a separate JSON file for collections. Rejected because the app already moved durable state to relational persistence and a file store would create divergent backup, deployment, and failure behavior.

3. Persist update snapshots as normalized saved-update rows with a deterministic key.

   The save request should include the collection id and the update snapshot fields already returned by `/api/updates`. The backend derives the deterministic update key from canonical source identity plus the update URL. The save endpoint requires an update URL; visible frontend updates already require one. Snapshot fields are stored on the saved-update row so a collection can display the saved item even if the source later removes or changes the update.

   Alternative considered: store only a reference to future `/api/updates` results. Rejected because saved updates could disappear when a feed rolls over, the selected update window changes, or source metadata changes.

4. Make saving idempotent per collection and update key.

   Add a uniqueness rule for `(collection_id, update_key)`. Saving an update that already exists in the target collection should return the existing saved item without changing its original `saved_at`. This avoids duplicate collection entries and preserves the meaning of save time.

   Alternative considered: update the snapshot and `saved_at` on repeated saves. Rejected because the ticket specifically wants the time the update was saved to the collection, and repeated button clicks should not move an old saved item to the top.

5. Keep collections fixed in code and persistence for this ticket.

   Define the fixed collection ids and display names in backend domain/application code, seed them in persistence, and have the UI render whatever the API returns. The UI should not expose create/delete controls.

   Alternative considered: hard-code collection cards only in the frontend. Rejected because the save API needs authoritative collection ids and future collection management should build on backend-owned collection records.

6. Add a `/api/collections` route group.

   Use `GET /api/collections` to list collections with saved updates, `POST /api/collections/{collection_id}/updates` to save an update snapshot, and `DELETE /api/collections/{collection_id}/updates/{update_key}` to remove a saved update. The public API grows, but a collection-specific namespace is clearer than overloading `/api/updates`, whose current purpose is source collection.

   Alternative considered: add collection fields to `/api/updates`. Rejected because collections are durable user state, while updates are transient source results.

7. Add a `collections` webapp route and per-update save controls.

   Extend `PageView`, `usePageRoute`, `TopNavigation`, and `LearningEnginePage` with a Collections page. Fetch collections with TanStack Query. On the Updates page, add compact save actions for the fixed collections on each update item. Mutations should invalidate or update the collections query and show the existing toast feedback.

   Alternative considered: embed collections below the Updates feed. Rejected because the ticket asks for a new Collections page and collection management will expand in future tickets.

## Risks / Trade-offs

- Public API and persistence surface area grows -> Keep endpoints collection-scoped and cover them with presentation and infrastructure tests.
- Deterministic keys may collide if a source republishes different content at the same URL -> Include source identity in the key and treat same-source same-URL saves as the same update, which matches common feed semantics.
- Snapshot columns duplicate update/source fields -> Accept duplication because collections must remain readable without recollecting transient updates.
- `SQLModel.metadata.create_all()` does not perform full migrations -> New tables can be created for this feature, but future schema changes may need an explicit migration approach if existing saved-update columns change.
- Repeated saves could feel like they should refresh content -> Preserve original `saved_at` and existing snapshot for idempotence; future ticket can add explicit refresh behavior if needed.

## Migration Plan

- Add new collection tables with `create_all()` through the existing `ensure_data_store()` path.
- Seed `see-later` and `liked` rows idempotently when the data store is ensured.
- No backfill is required because there are no persisted updates today.
- Rollback removes the UI/API usage; existing database rows would remain inert unless a later cleanup migration is introduced.

## Open Questions

- None. The key product ambiguity was resolved: saved collection entries store both an update snapshot and a deterministic update key.
