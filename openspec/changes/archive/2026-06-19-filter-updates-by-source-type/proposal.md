## Why

Users can see updates from several source types in the Updates and Collections pages, but there is no way to narrow those lists by source type. This makes mixed feeds harder to scan when the user wants to focus on one source channel such as feeds, pages, YouTube channels, X/Twitter accounts, or Spotify podcasts.

## What Changes

- Add a source type filter control to the Updates page.
- Add the same source type filter control to the Collections page.
- Filter already-loaded update lists client-side by each update snapshot's `source_interest.source_type`.
- Keep the default "all source types" view and existing refresh, save, remove, grouping, and loading/error behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `updates`: Users can filter visible updates by source type without changing update collection behavior.
- `collections`: Users can filter saved collection updates by source type without changing saved update persistence.

## Impact

- Webapp Updates and Collections page UI/state.
- Webapp source type labeling/filter helper code.
- Existing OpenSpec specs for Updates and Collections page behavior.
