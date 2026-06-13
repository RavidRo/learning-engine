## Context

Learning Engine already persists interests through an `InterestRepository` boundary and exposes the current editor payload through `/api/interests`. The React page fetches that payload with TanStack Query, filters soft-deleted interests for display, and writes the full list back when users edit, pause, or remove interests.

RAV-17 adds backup/restore behavior. The user decisions are:

- Import replaces the entire stored interest list.
- The file format is a versioned JSON envelope, not the raw `/api/interests` payload.
- Export includes all stored interests, including disabled and soft-deleted records.
- Import/export live behind backend API endpoints.
- Controls live in the Manage interests panel header.

## Goals / Non-Goals

**Goals:**

- Provide a JSON export that preserves the complete stored interest state.
- Validate imports through the backend before writing any replacement data.
- Keep the import/export file contract separate from the internal editor API payload.
- Make the UI flow discoverable in the Manage interests panel and explicit about replace-all behavior.

**Non-Goals:**

- Merge imported interests into the existing list.
- Resolve ID, name, or source conflicts between imported and existing interests.
- Support raw `{ "interests": [...] }` uploads through the import endpoint.
- Add cross-user sharing workflows beyond a file format that can support them later.
- Export collected updates, caches, source images, or other non-interest data.

## Decisions

1. Use backend endpoints for import/export.

   Add endpoints under the existing `/api/interests` namespace, for example `GET /api/interests/export` and `POST /api/interests/import`. This expands the public API surface, but it keeps file format parsing and validation at the presentation boundary where external JSON belongs. The alternative, frontend-only export/import using `/api/interests`, would avoid new endpoints but would duplicate envelope rules in React and make future format changes harder to centralize.

2. Define a versioned envelope around `InterestsPayload`.

   Version 1 should contain a fixed schema version, an export timestamp, and the existing interest payload data. A representative shape is:

   ```json
   {
     "schemaVersion": 1,
     "exportedAt": "2026-06-13T13:00:00Z",
     "interests": []
   }
   ```

   The envelope is an adapter contract. Internally, imported `interests` still become an `InterestsPayload` before repository writes. The alternative, exporting the raw current payload, is simpler but does not leave a clean path for future file versions or sharing metadata.

3. Import is all-or-nothing replacement.

   The import endpoint validates the envelope version and nested interests first. Only a fully valid file writes to the repository. This avoids partial imports and conflict resolution rules. The alternative, merge import, is intentionally out of scope because it requires policy for duplicate IDs, duplicate source IDs, soft-deleted records, and name conflicts.

4. Export all stored records.

   The export endpoint reads directly from `InterestRepository.read_interests()` and serializes the full returned payload, not the UI-filtered visible list. This preserves disabled and soft-deleted data as part of backup/restore. The UI can continue filtering after import.

5. Keep UI controls compact and explicit.

   Add export/import controls to the Manage interests panel header near the save status. Export downloads the backend response as a `.json` file. Import uses a file input, asks for explicit confirmation that current interests will be replaced, posts the selected file contents to the import endpoint, then updates or invalidates the interests query with the saved payload returned by the backend.

## Risks / Trade-offs

- Public endpoint growth -> Keep routes scoped under `/api/interests` and document the envelope as the stable file contract, while preserving existing `/api/interests` behavior.
- Accidental data loss on import -> Require explicit browser confirmation before upload and perform all-or-nothing server validation before replacement.
- Invalid or wrong JSON file -> Return a clear 400 response without writing changes.
- Future envelope changes -> Reject unsupported `schemaVersion` values now so later versions can be introduced deliberately.
- Timestamp nondeterminism in tests -> Inject or isolate timestamp creation where practical, or assert timestamp shape rather than exact wall-clock values.
