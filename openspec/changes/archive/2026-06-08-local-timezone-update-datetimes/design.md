## Context

RAV-7 targets the updates page. The current React component renders `update.published` directly in each update card, so users see the source-provided timestamp string rather than a local, readable display value.

The backend updates API already provides `published` as an optional string. This change should validate `published` with Zod's ISO datetime parser and transform it into a `Date` immediately after the updates response is fetched in the webapp API adapter, before data reaches the page render path.

## Goals / Non-Goals

**Goals:**

- Show update publication times in the viewer's local timezone.
- Use a compact, human-friendly date/time format that scans well inside update cards.
- Keep missing timestamps valid while treating invalid ISO datetime values as a user-visible update display error.
- Keep update card state free of raw timestamp strings by passing parsed `Date` values into the page.
- Keep the implementation local to the webapp unless existing code reveals a shared date helper already in use.

**Non-Goals:**

- Changing backend update collection, persistence, or API response shape.
- Normalizing source timestamps server-side.
- Adding user-configurable timezone or date format preferences.
- Introducing a new date/time dependency.

## Decisions

- Transform update publication timestamps in the original update schema.
  - Rationale: `published` is part of the update payload contract, so the schema should validate it directly with `z.iso.datetime()` and expose a `Date` instead of preserving a raw timestamp string.
  - Alternative considered: format timestamps in the backend. That would either use the server timezone or require sending client timezone information, which is unnecessary for this ticket.
  - Alternative considered: parse a raw update schema and derive a separate display label at fetch time. That would keep a raw timestamp layer in the client and serialize display too early.

- Use Zod's ISO datetime parser for validation and transformation, then platform `Intl.DateTimeFormat` APIs for local formatting during render.
  - Rationale: `z.iso.datetime()` matches the existing Zod schema layer and gives the API adapter a clear ISO string validation boundary before storing a `Date`. Formatting during render keeps localization at the presentation point.
  - Alternative considered: add a library such as date-fns. That would increase dependency surface for a narrow formatting requirement.

- Display nothing when `published` is missing and raise an update display error when parsing fails.
  - Rationale: missing timestamps are already optional, but an invalid timestamp means the app cannot satisfy the local-time display contract. The user should see that the update could not be shown correctly.
  - Alternative considered: display the unparsed source value when parsing fails. That would keep more source data visible, but it would hide the failure and violate the local-time display requirement.

- Expose only the parsed `Date` to the updates page after successful adaptation.
  - Rationale: the page does not need the source timestamp after successful adaptation, and storing the `Date` lets the UI serialize only when it needs a display string.
  - Alternative considered: carry both the source timestamp and a display label. That adds data the UI does not need.

## Risks / Trade-offs

- Source timestamps that are not valid ISO datetimes will be rejected -> show the user-facing update display error so the issue is explicit.
- Locale output can vary across environments -> verify behavior by asserting the formatter is called with local-timezone semantics rather than brittle exact strings where possible.
- Failing the whole updates response for one invalid timestamp may hide otherwise valid updates -> show a clear error message so users know the update list could not be displayed correctly instead of silently mixing raw and formatted time values.
- Very long locale-specific labels may affect compact card layout -> choose a concise formatter and verify the updates page remains visually stable.
