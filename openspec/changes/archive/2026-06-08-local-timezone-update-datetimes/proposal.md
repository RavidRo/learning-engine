## Why

Update cards currently show the raw `published` timestamp returned by each source, which can be hard to scan and may not reflect the viewer's local timezone. RAV-7 asks for update datetimes to appear as local, human-friendly values on the updates page.

## What Changes

- Parse each update's `published` value as an ISO datetime with Zod immediately after the updates response is fetched and validated by the webapp API adapter, storing it as a `Date` rather than a raw timestamp string.
- Use a concise, human-friendly date/time label that remains useful across recent and older updates.
- Preserve behavior for updates without a published timestamp by omitting the timestamp.
- Preserve the backend updates API shape and stored data; this change only affects presentation.
- Treat invalid ISO datetime source timestamps as update display failures and show a user-visible error instead of rendering the affected updates list.

## Capabilities

### New Capabilities

- `update-datetime-display`: Parses fetched update publication timestamps into `Date` values, renders local human-friendly display values, and reports timestamp display failures to the user.

### Modified Capabilities

None.

## Impact

- Webapp schemas/API adapter: validate fetched update timestamps as ISO datetimes and convert them into `Date` values before the updates page renders.
- Webapp updates page: render local timestamp labels from parsed `Date` values and show a clear error when update timestamp parsing fails.
- Webapp tests: cover local formatting at fetch/adaptation time, missing timestamps, and invalid ISO timestamp error behavior.
- Backend API: no request or response contract changes.
