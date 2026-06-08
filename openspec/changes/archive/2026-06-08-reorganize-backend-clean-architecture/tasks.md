## 1. Establish Layer Scaffolding

- [x] 1.1 Create backend package folders for `common`, `domain`, `application`, `infrastructure`, and `presentation` with minimal `__init__.py` files.
- [x] 1.2 Add application port protocols for source update collection, source image resolution, interest persistence, and any shared fetching boundary needed by existing use cases.
- [x] 1.3 Add compatibility imports only where needed to keep existing public module paths working during the staged migration, and mark each one for removal before completion.

## 2. Move Application Use Cases Behind Ports

- [x] 2.1 Move collect-updates orchestration into the application layer while preserving enabled-source selection, concurrency, timeframe filtering, deduplication, error reporting, and cache behavior.
- [x] 2.2 Replace direct provider imports in collect-updates orchestration with an injected source update collector or source collector registry port.
- [x] 2.3 Extract source image resolution policy into an application use case or application service that can be called by presentation and update collection.
- [x] 2.4 Update collector-focused tests to exercise application use cases through explicit dependencies instead of monkeypatching private provider functions where practical.

## 3. Move Infrastructure Adapters

- [x] 3.1 Move HTTP fetching implementation into the infrastructure layer while keeping the application-facing fetch protocol explicit.
- [x] 3.2 Move JSON-backed interest storage into the infrastructure layer and expose it through the interest repository port.
- [x] 3.3 Move feed, page, YouTube, Twitter, and Spotify update collectors into infrastructure source collector modules or an infrastructure dispatcher implementing the application port.
- [x] 3.4 Move provider-specific source image metadata fetching and parsing into infrastructure source image modules implementing the application source image resolver boundary.

## 4. Move Domain And Common Code

- [x] 4.1 Move Pydantic interest, source, update, and collection error models into the domain layer without introducing parallel dataclass models.
- [x] 4.2 Move timeframe, date parsing/formatting, markup stripping, and generic text helpers into the common layer.
- [x] 4.3 Update imports across application, infrastructure, presentation, and tests to use the new domain and common module locations.
- [x] 4.4 Ensure `common` does not import Learning Engine domain concepts, provider code, persistence code, HTTP framework code, or application use cases.

## 5. Move Presentation And Composition

- [x] 5.1 Move FastAPI app creation, route handlers, HTTP status mapping, lifespan wiring, and dependency composition into the presentation layer.
- [x] 5.2 Keep the existing backend entrypoint behavior working during presentation migration, using only temporary compatibility code that can be removed before completion.
- [x] 5.3 Update app and server tests to target the presentation entrypoint while preserving existing route behavior.

## 6. Verify Behavior And Architecture Readiness

- [x] 6.1 Run the narrowest relevant backend tests after each migration group.
- [x] 6.2 Remove temporary compatibility re-export modules once tests, entrypoints, and internal imports use the new package layout.
- [x] 6.3 Add dependency-direction enforcement as the final migration step.
- [x] 6.4 Run the backend or project check task before finishing the implementation.
