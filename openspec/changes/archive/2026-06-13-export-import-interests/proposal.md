## Why

Users need a reliable way to back up their Learning Engine interests and restore them later. A versioned import/export format also creates a controlled foundation for future interest sharing without coupling users to the internal persistence payload.

## What Changes

- Add an export capability that downloads all stored interests, including disabled and soft-deleted records, as a JSON file.
- Add an import capability that accepts only the versioned export envelope and replaces the entire stored interest list after validation.
- Add backend API endpoints for export and import so format handling and validation stay server-side.
- Add compact export/import controls to the Manage interests panel header, with explicit confirmation before import replaces existing interests.
- Preserve the existing `/api/interests` read/write contract for the current editor flow.

## Capabilities

### New Capabilities

- `interest-import-export`: Export all stored interests in a versioned JSON envelope and import that envelope as a full replacement.

### Modified Capabilities

- None.

## Impact

- Backend presentation/API layer gains export and import routes under `/api/interests`.
- Backend schema/model layer gains a versioned export envelope adapter around the existing `InterestsPayload`.
- Existing interest repository boundary continues to read and write the full validated payload.
- Web app gains download/upload actions in the Manage interests panel header and refreshes the interest cache after import.
- Tests should cover backend envelope validation, replace-all persistence behavior, frontend schema/API helpers, and UI controls where the existing test layer supports them.
