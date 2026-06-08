## Python & Code Style

- Use `None` for missing scalar values. Empty strings are content, not absence.

## Backend Architecture

The backend is organized into clean-architecture layers. Keep dependencies
flowing inward through explicit boundaries:

- `learning_engine/common`: generic utilities only. This layer must not know
  about Learning Engine domain concepts, application use cases, infrastructure
  adapters, provider APIs, persistence, or FastAPI.
- `learning_engine/domain`: Pydantic domain models and domain concepts. Keep
  domain models here rather than creating parallel DTOs unless a proposal
  explicitly chooses that trade-off.
- `learning_engine/application`: use cases and ports. Application code may
  depend on `domain` and `common`, and it should depend on external behavior
  through protocols in `application/ports.py`.
- `learning_engine/infrastructure`: adapters that implement application ports,
  such as HTTP fetching, JSON storage, source collectors, and source image
  provider resolution.
- `learning_engine/presentation`: FastAPI route handlers, HTTP status mapping,
  lifespan setup, and dependency composition.

Dependency direction:

- `presentation` composes `application` and `infrastructure`.
- `application` depends on `domain`, `common`, and its own ports.
- `infrastructure` may depend on `application` ports plus `domain` and
  `common`, but not on `presentation`.
- `domain` must not depend on `application`, `infrastructure`, or
  `presentation`.
- `common` must not depend on any other backend layer.

When adding tests, place them under the matching package in `tests/`
(`common`, `domain`, `application`, `infrastructure`, `presentation`, or
`architecture`). The architecture boundary test enforces dependency direction,
so update it deliberately if the intended architecture changes.
