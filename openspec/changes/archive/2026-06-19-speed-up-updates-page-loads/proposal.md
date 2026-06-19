## Why

The Updates page currently waits on backend collection work that can perform repeated network fetches per source before the page can finish loading. Users need the page to fully load updates quickly enough for routine use.

## What Changes

- Require the Updates page to fully load its updates view in under 4 seconds under the supported local development/runtime conditions.
- Reduce duplicate backend network work during update collection, especially when a source URL is fetched once for updates and again for source image metadata.
- Preserve the existing Updates page API shape, update grouping, error reporting, source image behavior, and collection actions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `updates`: Add a performance requirement for the Updates page to fully load within 4 seconds.

## Impact

- Backend update collection and HTTP fetching infrastructure.
- Existing in-memory update/source-fetch caching behavior.
- Backend tests for update collection, fetch caching, and API behavior.
