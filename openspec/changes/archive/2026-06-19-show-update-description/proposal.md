## Why

RAV-30 asks for update cards to show a description under each update title. The updates API already provides an optional `summary` field, but the Updates page currently hides it, making cards less informative than the Linear screenshot.

## What Changes

- Render each update's existing `summary` as a description directly under the title.
- Omit the description line when the summary is missing, null, or blank.
- Keep source metadata, publication timestamp, thumbnail, grouping, refresh, and save-to-collection behavior unchanged.
- Preserve the backend updates API shape and stored data; this change only affects webapp presentation.

## Capabilities

### New Capabilities

### Modified Capabilities

- `updates`: Update cards display an optional description below the title.

## Impact

- Webapp Updates page card markup and styling.
- Existing `updates` OpenSpec capability.
- No backend API, persistence, service, datastore, dependency, or security changes.

Assumption recorded from RAV-30 and its screenshot: the update description is the already-fetched `summary` field, placed between the title and existing metadata.
