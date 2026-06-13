## 1. Backend Domain and Application

- [x] 1.1 Add collection domain models for fixed collections, saved update snapshots, saved update payloads, and collection list responses.
- [x] 1.2 Add deterministic update key derivation that requires a source identity and update URL.
- [x] 1.3 Add a `CollectionRepository` application port with list, save, and remove operations.
- [x] 1.4 Add application use cases for listing fixed collections, saving update snapshots idempotently, and removing saved updates.
- [x] 1.5 Add domain and application tests for key derivation, fixed collection ids, idempotent saves, per-collection membership, and snapshot preservation.

## 2. Backend Persistence

- [x] 2.1 Add SQLModel tables for collections and saved collection updates to the existing storage metadata.
- [x] 2.2 Seed `see-later` and `liked` collections idempotently in `ensure_data_store()`.
- [x] 2.3 Implement collection repository methods on the existing SQLModel store.
- [x] 2.4 Enforce uniqueness for `(collection_id, update_key)` while preserving the original `saved_at` on repeated saves.
- [x] 2.5 Add infrastructure tests for table writes, repeated initialization, ordering by `saved_at`, unknown collection rejection, idempotent saves, and removal behavior.

## 3. Backend API

- [x] 3.1 Add presentation schemas for collection list responses, saved update snapshots, save requests, and save/remove responses.
- [x] 3.2 Add `/api/collections` routes for listing collections, saving an update to a collection, and removing a saved update.
- [x] 3.3 Compose the collection repository in FastAPI app state using the existing store.
- [x] 3.4 Add FastAPI tests for listing fixed collections, saving snapshots, repeated saves, unknown collection errors, ordered responses, and removal.

## 4. Webapp API and State

- [x] 4.1 Add collection Zod schemas and TypeScript types.
- [x] 4.2 Add API helpers for fetching collections, saving an update to a collection, and removing a saved update.
- [x] 4.3 Add TanStack Query state and mutations for collections, including cache invalidation or cache updates after save/remove.
- [x] 4.4 Extend page routing, navigation, and page state with a `collections` view.

## 5. Webapp UI

- [x] 5.1 Add save-to-collection controls to each visible Updates page item without changing existing update grouping or refresh behavior.
- [x] 5.2 Add a Collections page that displays the fixed collections and saved updates ordered by save time.
- [x] 5.3 Add remove controls for saved updates on the Collections page.
- [x] 5.4 Add responsive styles so update cards, save controls, collection cards, and remove controls do not overlap on narrow viewports.

## 6. Verification

- [x] 6.1 Run the narrowest useful backend tests while implementing storage, application, and API behavior.
- [x] 6.2 Run the webapp checks after frontend changes.
- [x] 6.3 Run `task check` before finishing when feasible.
- [x] 6.4 Manually verify the Updates and Collections page flows locally and capture screenshots for the eventual PR because the change affects the visual interface.
