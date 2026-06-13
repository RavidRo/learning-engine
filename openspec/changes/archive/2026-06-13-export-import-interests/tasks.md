## 1. Backend Import/Export Contract

- [x] 1.1 Add a versioned interest export envelope schema that wraps `InterestsPayload` with `schemaVersion` and `exportedAt`.
- [x] 1.2 Add backend unit coverage for serializing all stored interests, including disabled and soft-deleted records, into the version 1 envelope.
- [x] 1.3 Add backend validation coverage proving malformed JSON, raw `{ "interests": [...] }` payloads, unsupported schema versions, and invalid nested interests are rejected without writing.

## 2. Backend API Endpoints

- [x] 2.1 Add `GET /api/interests/export` to read from the existing interest repository and return the versioned JSON envelope.
- [x] 2.2 Add `POST /api/interests/import` to validate the versioned envelope, replace the full repository payload only after successful validation, and return the saved payload.
- [x] 2.3 Add FastAPI route tests for successful export, successful replace-all import, and failed import preserving the previous repository state.

## 3. Web Import/Export Actions

- [x] 3.1 Add web API helpers for downloading the export JSON and uploading a selected import file to the backend import endpoint.
- [x] 3.2 Add compact Export and Import controls to the Manage interests panel header next to the save status.
- [x] 3.3 Require explicit confirmation before uploading an import file and clear the file input after each import attempt.
- [x] 3.4 Refresh or update the TanStack Query interests cache from the import response so the displayed active interests match the imported state.

## 4. Verification

- [x] 4.1 Add or update frontend tests if the current web test layer covers learning-engine page actions.
- [x] 4.2 Run the narrowest relevant backend and web checks during implementation.
- [x] 4.3 Run `task check` before finishing when feasible.
