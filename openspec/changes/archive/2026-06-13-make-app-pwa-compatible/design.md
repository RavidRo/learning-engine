## Context

The webapp is a Vite React app with a minimal `site.webmanifest`, static favicons, and a server-backed `/api` contract for interests, updates, and source image resolution. The primary phone workflow is opening the app to the Updates view and checking recent source activity. Interest management remains available, but it is form-heavy and depends on live backend saves.

This change introduces a PWA layer around the existing frontend without changing backend APIs or persistence. The main architectural boundary is that the service worker owns only frontend app-shell caching. Backend data remains live server data, so offline editing and API-response caching are intentionally out of scope.

## Goals / Non-Goals

**Goals:**

- Make the webapp installable on supported mobile browsers.
- Launch installed sessions at `/updates`.
- Precache versioned frontend build assets so the app shell can load with poor or missing network connectivity.
- Prompt users before applying a newly deployed frontend build.
- Present global offline and update status below the existing topbar.
- Disable actions that require network while offline.
- Improve narrow-screen layout resilience without replacing the current topbar.

**Non-Goals:**

- No offline editing, background sync, conflict resolution, or client-side datastore.
- No service-worker caching of `/api` responses.
- No install banner or custom install prompt in the app.
- No backend API, storage, or security model changes.

## Decisions

### Use `vite-plugin-pwa` with generated Workbox service worker

Use `vite-plugin-pwa` to integrate service worker generation into the existing Vite build. Configure the generated service worker to precache frontend build assets and the manifest/icons, relying on Workbox's build-time revisioning and outdated-cache cleanup.

Alternative considered: a project-owned handwritten service worker. That would reduce dependency count, but it would make cache lifecycle, asset revisioning, and update detection easier to get subtly wrong. The plugin is a conventional Vite solution for this exact asset precaching problem.

### Keep service worker scope to frontend assets only

Do not runtime-cache `/api/interests`, `/api/updates`, or `/api/source-image`. Network-backed data should fail visibly when offline rather than producing stale or misleading state. Existing React Query state may still keep already-loaded data visible during a running session, but it is not promoted to a durable offline data source.

Alternative considered: cache selected GET API responses. That would improve read-through behavior, but it would create separate freshness and invalidation semantics from the backend and would not solve edits. It is deferred until the app has a real offline data model.

### Use prompt-style updates

Register the service worker with prompt update behavior. When a new service worker is waiting, show a compact banner with an explicit refresh action. Avoid automatic page reload because users may be editing interest forms.

Alternative considered: automatic update reload. It is simpler, but it can discard in-progress form input and gives the user less control over when a deployed version takes over.

### Add an app-level network/update state

Add a small global banner directly below the existing topbar. It should show offline status whenever `navigator.onLine` reports offline, and update availability when the service worker reports a waiting update. If both apply, offline state should take priority because the refresh action cannot reliably complete without network.

Network-required actions should receive a shared `isOffline` signal and disable themselves while offline:
- update refresh;
- create/update/delete/toggle interest saves;
- source image lookup.

### Complete install metadata and icons

Replace the minimal manifest contents with install-focused metadata: `name`, `short_name`, `description`, `start_url: "/updates"`, `scope: "/"`, `display: "standalone"`, theme/background colors, and icon entries for install-grade 192px and 512px PNG assets, including maskable variants. Keep iOS-compatible apple touch icon metadata in `index.html`.

### Mobile layout polish remains responsive CSS

Keep the current topbar. Use responsive CSS to reduce shell margins, stack dense panels, preserve readable update cards, add safe-area padding, and prevent horizontal overflow on phone widths.

## Risks / Trade-offs

- New build dependency can add setup friction -> keep the dependency scoped to the webapp build and verify through `task web:build` / `task web:check`.
- Service worker bugs can make old assets linger -> use Workbox-generated precaching and cleanup rather than custom cache code.
- Offline state from `navigator.onLine` is not a perfect reachability check -> treat it as a UX guardrail and keep API error handling intact for server-side or captive-network failures.
- Installed app updates are not instant -> prompt update mode intentionally waits for user action so active form work is not lost.
- Generated icons can look poor if derived from a tiny favicon -> generate or recreate icons from the vector favicon where possible and verify install asset dimensions.
