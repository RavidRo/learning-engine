## Why

Learning Engine should be easy to launch and use from a phone, especially for quickly checking updates. The app already has a minimal manifest, but it is not yet a reliable Progressive Web App with install-grade icons, app-shell caching, explicit update handling, or clear offline behavior.

## What Changes

- Make the webapp installable as a PWA with a complete manifest, phone-appropriate app metadata, and proper 192px/512px maskable icons.
- Set the installed app launch target to the Updates view.
- Add a conservative Workbox-backed service worker through `vite-plugin-pwa` that precaches versioned frontend build assets only.
- Use prompt-style service worker updates, showing a compact global "Update available" banner with an explicit refresh action when a new build is ready.
- Add a small global offline/update banner directly below the existing topbar.
- Keep the current topbar navigation unchanged.
- Disable network-required actions while offline, including update refresh, interest saving, and source image lookup.
- Improve mobile layout resilience for phone use without introducing offline editing or background sync.

## Capabilities

### New Capabilities

- `pwa-installability`: Defines installability, app-shell caching, update prompts, offline state, and mobile behavior for the webapp.

### Modified Capabilities

- None.

## Impact

- Affects the Vite React webapp, public PWA assets, manifest metadata, service worker registration, and mobile CSS.
- Adds a web build dependency for `vite-plugin-pwa` and Workbox-generated precaching.
- Does not change backend APIs, persisted data shape, authentication/security behavior, or server-side storage.
