## Why

RAV-14 asks for updates to be saved into named collections so the user can return to important updates later. The current Updates page only shows transient source-collection results, so saved items need their own persisted representation with the time they were saved.

## What Changes

- Add a persisted `Collection` domain capability with two initial fixed collections: `See Later` and `Liked`.
- Save update membership with both a deterministic update key and a snapshot of the update as it appeared when saved.
- Store the timestamp for when an update is saved to a collection and sort collection contents by that save time in the UI.
- Add backend API endpoints for listing collections, adding an update snapshot to a collection, and removing an update from a collection.
- Add a Collections page that lists the fixed collections and displays saved updates for each collection.
- Add controls on the Updates page so a user can save any visible update to either fixed collection.
- Defer collection creation, deletion, and renaming to a future ticket.

## Capabilities

### New Capabilities

- `update-collections`: Persist fixed update collections, allow saving and removing update snapshots, and display saved collection contents ordered by save time.

### Modified Capabilities

- `updates-page-layout`: The Updates page gains save-to-collection actions for each update while preserving existing refresh, grouping, filtering window, error, and empty-state behavior.

## Impact

- Backend domain: add collection and saved-update models alongside existing update models.
- Backend application: add a collection repository port and use cases for listing collections and managing saved updates.
- Backend infrastructure: extend SQLModel persistence with collection and saved-update tables, seeded fixed collections, uniqueness rules, and `saved_at` timestamps.
- Backend presentation: add `/api/collections` routes and request/response schemas.
- Webapp API and schemas: add collection payload validation and mutations.
- Webapp routing/navigation: add a `collections` page view.
- Webapp Updates page: add per-update save actions that target the fixed collections.
- Webapp Collections page: render saved updates ordered by save time and support removing saved updates.
- Tests: add domain/application/presentation/infrastructure coverage for collection behavior and frontend checks for collection parsing and page state where existing test layers allow it.
