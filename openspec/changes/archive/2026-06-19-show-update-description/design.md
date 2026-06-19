## Context

RAV-30 targets the Updates page. The webapp schema already accepts `summary` on update payloads, while `UpdateItem` currently renders only the title, source metadata, timestamp, thumbnail, and collection actions.

The ticket screenshot shows a short text line under the title and above the source/type metadata. This maps to the existing `summary` field without requiring backend, API, or persistence changes.

## Goals / Non-Goals

**Goals:**

- Show a visible update description directly under the update title when a non-blank summary is available.
- Keep the update card compact and readable with the existing metadata and collection controls.
- Preserve all current update fetching, grouping, error, empty-state, timestamp, thumbnail, and collection behaviors.

**Non-Goals:**

- Changing how updates are collected, summarized, stored, or returned by the backend.
- Adding a new update payload field.
- Rendering placeholder description text when no summary exists.

## Decisions

- Use `update.summary` as the description source.
  - Rationale: the client schema already models `summary`, and the ticket asks only to show the description under the title.
  - Alternative considered: introduce a separate `description` field. That would alter the API contract for a presentation-only change and is unnecessary.
- Trim and omit blank summaries before rendering.
  - Rationale: blank source summaries should not create empty vertical space in update cards.
  - Alternative considered: render any non-null string. That would expose whitespace-only payloads as broken-looking card content.
- Add card-local styling for the description.
  - Rationale: the description should be visually subordinate to the title but more prominent than metadata, matching the screenshot hierarchy.
  - Alternative considered: reuse metadata styling. That would make the description look like source/date data rather than content.

## Risks / Trade-offs

- Long summaries could make update cards taller -> constrain the description to a small number of lines and allow wrapping without overlapping controls.
- Some source summaries may duplicate titles -> render the payload as-is because deduplication would be content policy outside this UI request.
- The card layout changes visually -> include PR screenshot evidence if local rendering can be produced.
