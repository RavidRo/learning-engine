## ADDED Requirements

### Requirement: Backend layers are organized by responsibility
The backend SHALL organize code into layers with distinct responsibilities: common utilities, domain models, application use cases and ports, infrastructure adapters, and presentation wiring.

#### Scenario: Developer locates application orchestration
- **WHEN** a developer needs to modify source collection orchestration or source image use-case policy
- **THEN** the relevant use-case code is located in the application layer rather than in provider adapters or FastAPI route handlers

#### Scenario: Developer locates generic helpers
- **WHEN** a developer needs to modify generic timeframe, date parsing, markup stripping, or text helper behavior
- **THEN** the relevant helper code is located in the common layer rather than in the domain layer

### Requirement: Application code depends on ports for external behavior
Application use cases SHALL depend on explicit ports for external behavior such as interest persistence, source update collection, source image provider resolution, and network-backed provider access.

#### Scenario: Source provider implementation changes
- **WHEN** a source provider implementation changes for feeds, pages, YouTube, Twitter, or Spotify
- **THEN** the collect-updates use case continues to depend on an application port rather than importing the provider implementation directly

#### Scenario: Interest persistence implementation changes
- **WHEN** the interest persistence implementation changes
- **THEN** presentation and application code use the repository boundary rather than reaching through to storage implementation details

### Requirement: Source image resolution is an application use case
The backend SHALL expose source image resolution as application-level behavior while keeping provider-specific metadata fetching and parsing in infrastructure.

#### Scenario: Source image endpoint resolves an image
- **WHEN** the presentation layer handles a source image request
- **THEN** it invokes the application source-image use case and maps the result or application error to the existing HTTP response contract

#### Scenario: Source image provider metadata changes
- **WHEN** provider-specific metadata fetching or parsing changes for a source type
- **THEN** the change is isolated to infrastructure provider code without moving use-case policy into that provider module

### Requirement: Public backend behavior is preserved during migration
The migration SHALL preserve existing public HTTP routes, response shapes, source collection behavior, source image resolution behavior, cache behavior, and JSON interest persistence behavior.

#### Scenario: Existing API client calls backend routes
- **WHEN** an existing client calls the health, interests, source-image, or updates routes
- **THEN** the backend returns the same externally observable response contract as before the migration

#### Scenario: Existing collection tests exercise behavior
- **WHEN** existing tests cover enabled-source selection, source collection, timeframe filtering, deduplication, source image fallback, cache reuse, and collection errors
- **THEN** those behaviors continue to pass under the reorganized architecture

### Requirement: Dependency direction is documented and enforceable
The backend architecture SHALL define and enforce this dependency direction by the end of the migration: presentation may compose application and infrastructure, application may depend on domain and common plus its own ports, infrastructure may implement application ports using domain and common, and domain/common must not depend on application, infrastructure, or presentation.

#### Scenario: Developer adds a new import
- **WHEN** a developer adds a new import across backend layers
- **THEN** the intended architecture provides a clear rule for whether that import is allowed

#### Scenario: Migration completes
- **WHEN** the clean-architecture migration is complete
- **THEN** dependency-direction enforcement prevents disallowed imports across backend layers
