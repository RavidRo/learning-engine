## Why

The backend currently has useful separation by module, but application orchestration, provider dispatch, persistence access, presentation wiring, and shared utilities are still coupled through implicit imports. Reorganizing around explicit clean-architecture layers will make source collection and source image resolution easier to evolve while preserving the current API behavior.

## What Changes

- Introduce a staged backend package organization around `common`, `domain`, `application`, `infrastructure`, and `presentation` layers.
- Keep Pydantic models as the domain model representation to avoid unnecessary mapping complexity.
- Treat source image resolution as an application use case, with low-level provider metadata fetching and parsing implemented in infrastructure.
- Introduce explicit application ports for persistence, source update collection, source image resolution, and related external dependencies before broad file movement.
- Preserve existing public API routes, response shapes, source collection behavior, cache behavior, and source image behavior during the migration.
- Add dependency-direction enforcement as the final migration step after the folder organization, ports, and import cleanup are in place.

## Capabilities

### New Capabilities
- `backend-architecture-boundaries`: Defines the backend layering, dependency direction, and architectural constraints for organizing domain models, common utilities, application use cases, infrastructure adapters, and presentation wiring.

### Modified Capabilities
- None.

## Impact

- Affected code includes `backend/learning_engine/app.py`, `collector.py`, `models.py`, `storage.py`, `fetching.py`, `source_images.py`, `sources/*`, `dates.py`, `text.py`, and `timeframe/*`.
- Existing backend tests will need import updates as modules move; any compatibility shims introduced during migration should be removed before completion.
- No public HTTP API changes are intended.
- No datastore, service, or dependency changes are required for the initial migration.
- The final migration step will add an import-boundary verification tool or test.
