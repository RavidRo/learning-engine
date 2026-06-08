## Context

The backend currently exposes a FastAPI app, reads and writes JSON-backed interests, collects updates from multiple source providers, resolves source images, and returns API response models. The existing modules are reasonably small, but the boundaries are implicit: `collector.py` imports provider-specific modules directly, `app.py` handles presentation and composition while also reaching into storage, and source image resolution mixes use-case policy with low-level provider metadata details.

The desired direction is a clean-architecture organization that starts with folders and explicit ports, then finishes by enforcing dependency direction. Pydantic models will remain the domain model representation because separate domain dataclasses and API schemas would add mapping complexity without enough current benefit.

## Goals / Non-Goals

**Goals:**

- Organize backend code into `common`, `domain`, `application`, `infrastructure`, and `presentation` layers.
- Make application use cases depend on explicit ports instead of provider implementation modules.
- Preserve current HTTP routes, response shapes, source collection semantics, cache behavior, source image behavior, and persistence behavior.
- Treat source image resolution as an application use case while keeping provider-specific metadata fetching and parsing in infrastructure.
- Keep generic utilities such as timeframe handling, date parsing, markup stripping, and generic text helpers outside the domain layer.
- Add dependency-direction enforcement as the final migration step.

**Non-Goals:**

- Replacing Pydantic domain models with separate dataclasses.
- Changing the public API contract or frontend integration.
- Changing persistence technology or introducing a service/datastore.
- Rewriting provider collection algorithms beyond what is needed to move them behind ports.
- Adding dependency enforcement before the migration has stable module boundaries.

## Decisions

### Use `common` for generic primitives and low-level helpers

`Timeframe`, date parsing/formatting helpers, markup stripping, and generic text matching will move toward a `common` layer rather than `domain`. These utilities do not name Learning Engine concepts and should remain usable from any layer without creating domain coupling.

Alternative considered: place these helpers in `domain` because domain rules use them. This would make `domain` a mixed bucket of business concepts and generic helpers, which weakens the meaning of the layer.

### Keep Pydantic models as domain models

Existing Pydantic models such as interests, sources, collected updates, updates, and collection errors will remain the model representation. The migration should reorganize them under the domain layer when appropriate, but it should not introduce parallel domain dataclasses.

Alternative considered: split pure domain dataclasses from FastAPI/Pydantic schemas. This would create cleaner theoretical boundaries, but current API and storage behavior already rely on Pydantic validation, aliases, and serialization. The added mapper surface is not justified for this stage.

### Create application ports before broad file movement

The first implementation step should introduce explicit ports for source update collection, source image resolution, interest persistence, and external fetching or provider dispatch where useful. The collect-updates use case can then depend on protocols instead of importing concrete provider modules.

Alternative considered: move files into new folders first. That creates visible structure quickly, but risks preserving the same dependency tangle under new names.

### Model source image resolution as an application use case

Source image resolution is used by multiple workflows and has user-facing behavior. The application layer should own use-case policy, including whether an image miss is acceptable and how known resolver failures are represented. Infrastructure should own provider-specific details such as YouTube page metadata, Spotify API response shapes, feed metadata, page metadata, and HTTP-provider failure classification.

Alternative considered: keep source image resolution entirely in infrastructure. This would hide a meaningful use case behind an adapter and keep collection policy coupled to provider mechanics.

### Remove compatibility shims during the migration

Existing imports may be preserved temporarily through thin re-export modules such as `learning_engine.collector` or `learning_engine.app` while internal code moves to `application` and `presentation`. These shims are short-lived migration scaffolding and should be removed as soon as tests, entrypoints, and internal imports use the new locations.

Alternative considered: perform one large import-breaking move. That could produce the desired final tree faster, but it increases review risk and makes behavioral regressions harder to isolate.

### Add dependency enforcement as the final migration step

The migration should end by enforcing the intended dependency direction after the package boundaries are in place and compatibility shims have been removed. Enforcement can use an import-boundary test or tool, but it should be part of this change rather than left as a separate follow-up.

Alternative considered: add enforcement first. That would require encoding boundaries before the code has been moved and would likely create noisy exceptions.

## Risks / Trade-offs

- [Risk] File moves create noisy diffs and import churn. → Mitigation: introduce ports first, use compatibility shims, and migrate tests alongside each step.
- [Risk] `common` becomes a dumping ground. → Mitigation: keep `common` restricted to generic helpers that do not know about interests, sources, collection, storage, HTTP frameworks, or providers.
- [Risk] Application ports become too abstract for the current app size. → Mitigation: add only ports that correspond to existing external boundaries or provider dispatch points.
- [Risk] Calling one use case from another could make orchestration hard to follow. → Mitigation: initially share a source image resolver port between use cases, then revisit whether a dedicated use-case call reads better after implementation.
- [Risk] Temporary compatibility shims can linger. → Mitigation: require shim removal before dependency-direction enforcement is added.

## Migration Plan

1. Add new package folders for `common`, `domain`, `application`, `infrastructure`, and `presentation` with minimal public surfaces.
2. Introduce application ports and adjust collection orchestration to depend on those ports.
3. Move source update provider modules behind infrastructure collectors or a dispatcher.
4. Split source image use-case policy from provider-specific resolver implementation.
5. Move generic helpers into `common` and domain models into `domain`, updating imports incrementally.
6. Move FastAPI creation and route handling into `presentation`, leaving only a temporary entrypoint compatibility module if needed.
7. Update tests to target application use cases, infrastructure adapters, and presentation routes through the new boundaries.
8. Remove temporary compatibility re-exports after tests and entrypoints use the new package layout.
9. Add dependency-direction enforcement as the final migration step.
10. Run the backend verification tasks and then the project check.

Rollback is straightforward because the migration preserves behavior and can be reverted by module group if a stage introduces regressions.

## Open Questions

- After seeing the first implementation, should collection call a source-image use case directly or should both collection and the endpoint share a lower-level application port?
