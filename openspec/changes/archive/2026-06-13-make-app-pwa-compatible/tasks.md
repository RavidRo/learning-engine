## 1. PWA Build Setup

- [x] 1.1 Add `vite-plugin-pwa` to the webapp dev dependencies and refresh `webapp/pnpm-lock.yaml`.
- [x] 1.2 Configure `VitePWA` in `webapp/vite.config.ts` with prompt update behavior, Workbox precaching, outdated cache cleanup, and a manifest that launches at `/updates`.
- [x] 1.3 Add TypeScript support for `virtual:pwa-register` imports.

## 2. Install Assets and Metadata

- [x] 2.1 Generate install-grade 192px and 512px PNG icons from the app mark, including maskable variants.
- [x] 2.2 Update public manifest/icon references and `webapp/index.html` metadata for install surfaces and iOS home-screen behavior.
- [x] 2.3 Verify production build output includes the manifest, service worker, precache manifest, and referenced icon assets.

## 3. Service Worker Update UX

- [x] 3.1 Register the service worker from the webapp entry point and expose update availability through React state.
- [x] 3.2 Add a compact global status banner below the existing topbar for update availability.
- [x] 3.3 Wire the banner refresh action to activate the waiting service worker and reload into the new build.

## 4. Offline State and Action Guards

- [x] 4.1 Add a browser network status hook using online/offline events with cleanup.
- [x] 4.2 Show a compact global offline banner below the existing topbar, taking priority over the update banner when offline.
- [x] 4.3 Disable Updates refresh while offline and provide accessible text indicating that a connection is required.
- [x] 4.4 Prevent create, update, delete, and toggle interest saves while offline before save requests are sent.
- [x] 4.5 Prevent automatic source image preview lookup while offline and show a connection-required preview message.
- [x] 4.6 Keep existing API error handling for non-offline network/server failures.

## 5. Phone Layout Polish

- [x] 5.1 Adjust responsive CSS so the shell, hero, topbar, update header controls, summaries, and update cards fit narrow phone viewports without horizontal overflow.
- [x] 5.2 Adjust Manage interests responsive CSS so editor fields, source cards, and interest cards stack cleanly with phone-usable tap targets.
- [x] 5.3 Add safe-area padding for standalone mobile display without changing the current topbar navigation model.

## 6. Verification

- [x] 6.1 Add or update focused tests for offline state behavior, disabled network actions, and update banner rendering where the current web test layer supports it. No current web test layer exists; covered by build/check verification.
- [x] 6.2 Run `task web:build` to verify PWA build artifacts are generated.
- [x] 6.3 Run `task web:check` for frontend linting, formatting, typing, and analysis.
- [x] 6.4 Run `task check` before finishing when feasible. Passed with `UV_PYTHON=/usr/bin/python3.14`; default interpreter selected unsupported `python3.14t`.
- [x] 6.5 Capture desktop and mobile screenshots of changed UI states for the PR description.
