## Context

The Updates page renders summary statistics in an `UpdatesSummary` aside inside `.updates-layout`, beside `.updates-feed`. On wider screens this creates a persistent left column, leaving less room for update groups, source error details, titles, and metadata. The Linear request asks for those statistics to move to the top.

The change is confined to the webapp presentation layer. The update payload already contains every value needed by the summary, and no backend contract changes are needed.

## Goals / Non-Goals

**Goals:**
- Present the three existing summary statistics above the updates feed.
- Allow update groups, callouts, and empty states to use the full panel width below the summary.
- Keep the existing header controls, refresh state, grouping, error, and empty-state behavior unchanged.
- Preserve clean wrapping on tablet and mobile widths.

**Non-Goals:**
- Change how updates are collected, grouped, sorted, or counted.
- Add new statistics or remove existing statistics.
- Introduce new components, dependencies, routes, or backend APIs.
- Redesign unrelated Learning Engine page sections.

## Decisions

- Keep `UpdatesSummary` in `UpdatesPage.tsx` and move only its placement in the JSX.
  - Rationale: The summary is already local to the page and uses the existing `UpdatesPayload`; moving it avoids a new abstraction for a localized layout fix.
  - Alternative considered: Extract a reusable stats component. Rejected because there is no current second use and it would broaden the change.

- Change `.updates-layout` from a two-column grid to a single-column content stack.
  - Rationale: The feed should receive the available width after the summary moves above it.
  - Alternative considered: Keep the grid and position the summary across columns. Rejected because it preserves unnecessary layout complexity for a page-specific stack.

- Style `.updates-summary` as a responsive row/grid of summary boxes.
  - Rationale: The statistics remain visible near the top while wrapping naturally on smaller viewports.
  - Alternative considered: Put summary boxes into the existing panel header. Rejected because header actions already include the date selector and refresh button; adding counters there would crowd the controls.

- Keep the Updates panel header terse and remove repeated context from the visible heading area.
  - Rationale: The selected time window is already visible in the date selector, and update grouping is visible in the feed cards, so repeating both costs vertical space without adding decision-making value.
  - Alternative considered: Keep the heading but reduce its font size. Rejected because the text remains redundant even when smaller.

- Place loaded summary statistics in the header row opposite the update controls.
  - Rationale: After removing the redundant title text, the top-left header area is the best place for compact status information and removes the extra summary strip from the content flow.
  - Alternative considered: Keep the compact summary as its own row. Rejected because it still consumes vertical space and leaves the header's left side underused.

## Risks / Trade-offs

- Summary boxes could compete visually with source error callouts if spacing is too tight -> Keep a clear gap between the summary row and feed content.
- Mobile screens could produce narrow summary boxes -> Use responsive grid behavior that stacks the boxes when needed.
- Existing screenshot expectations may change -> Verify the webapp build/checks and review the Updates page visually during implementation.
