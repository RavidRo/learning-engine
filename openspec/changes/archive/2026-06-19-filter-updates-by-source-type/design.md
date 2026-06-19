## Context

The backend already includes canonical source type values on update snapshots and saved collection snapshots. The current Updates page fetches updates by date window and then groups visible updates by interest. The Collections page renders saved updates from persisted snapshots. Both pages already receive enough source type metadata to filter in the browser.

## Goals / Non-Goals

**Goals:**

- Add source type filtering to the Updates and Collections pages.
- Preserve the existing backend API, update collection, saved collection persistence, and all-source defaults.

**Non-Goals:**

- Adding server-side source type query parameters.
- Persisting the selected source type filter.
- Changing source type canonical values.

## Decisions

Add a client-side source type filter state for the Updates and Collections page surfaces, defaulting to all source types. The filter will compare the canonical `source_interest.source_type` field on each update or saved update snapshot.

This avoids adding API query parameters or persistence changes for a narrow UI filter. The trade-off is that filtering only applies to already-loaded data: the Updates page still collects all source types for the selected date window, and the Collections page still loads all saved updates before narrowing the display. That matches the ticket's scan/filter goal while preserving existing backend contracts and cache behavior.

The control will use the existing select-control pattern near the page header actions. The Updates page summary continues to describe the fetched payload, while groups and empty state reflect the active visible filter. The Collections page keeps each fixed collection visible and filters the saved updates within each collection, including the per-collection visible count.

## Risks / Trade-offs

- Client-side filtering does not reduce backend update collection work. This is acceptable for the current UX-only requirement and avoids a public API change.
- The filter option list must stay aligned with canonical source types. A shared frontend source type metadata helper keeps page controls and labels in one place.
