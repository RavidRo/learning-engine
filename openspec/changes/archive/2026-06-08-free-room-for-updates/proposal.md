## Why

The Updates page currently reserves a left-side column for summary statistics, which reduces the horizontal space available for grouped update content. Moving the summary to the top makes the feed easier to scan while preserving the same information and controls.

## What Changes

- Move the Updates summary statistics from the left side of the feed to a top summary row below the page header.
- Let the updates feed use the full available panel width once summary statistics are shown above it.
- Keep the existing update counts, source error messaging, empty state, refresh behavior, and update grouping behavior unchanged.
- Preserve responsive behavior so the summary row wraps or stacks cleanly on narrow screens.

## Capabilities

### New Capabilities
- `updates-page-layout`: Covers the required layout behavior for the Updates page summary and feed.

### Modified Capabilities

## Impact

- Affected code: `webapp/src/pages/learning-engine/UpdatesPage.tsx` and related styles in `webapp/src/styles.css`.
- APIs: No backend API, schema, or persistence changes.
- Dependencies: No new runtime or development dependencies.
