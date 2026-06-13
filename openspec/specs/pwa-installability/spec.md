## Purpose

Define Progressive Web App installability, app-shell caching, update prompting, connection-unavailable state, and phone layout behavior for the webapp.

## Requirements

### Requirement: Webapp is installable as a PWA
The webapp SHALL provide install-grade PWA metadata and assets for supported mobile browsers.

#### Scenario: Browser reads app metadata
- **WHEN** a supported browser loads the webapp
- **THEN** the linked web app manifest includes the app name, short name, description, scope, standalone display mode, theme color, background color, and start URL

#### Scenario: Installed app launches
- **WHEN** a user opens the installed app from a phone home screen
- **THEN** the app launches to the Updates view using `/updates` as its start URL

#### Scenario: Browser reads install icons
- **WHEN** a supported browser evaluates installability
- **THEN** the manifest references valid 192px and 512px PNG icons, including maskable icon variants

### Requirement: App shell is cached without caching API data
The webapp SHALL cache frontend app-shell assets for offline loading and MUST NOT service-worker-cache backend API responses.

#### Scenario: Frontend assets are built
- **WHEN** the webapp production build runs
- **THEN** the service worker precache includes versioned frontend build assets needed to load the app shell

#### Scenario: API request is made
- **WHEN** the app requests `/api/interests`, `/api/updates`, or `/api/source-image`
- **THEN** the service worker does not serve a cached API response for that request

#### Scenario: App opens without network after prior install
- **WHEN** the installed app opens without network after the app shell was cached
- **THEN** the frontend shell loads and presents a clear connection-unavailable state instead of a browser network failure page

### Requirement: New deployed builds are applied by user prompt
The webapp SHALL notify the user when a new service worker version is waiting and SHALL apply it only after an explicit refresh action.

#### Scenario: New build is available
- **WHEN** the browser detects a newly deployed service worker version
- **THEN** the app displays a compact global update banner below the topbar

#### Scenario: User accepts update
- **WHEN** the update banner is visible and the user activates its refresh action
- **THEN** the app tells the waiting service worker to activate and reloads into the new build

#### Scenario: User has not accepted update
- **WHEN** a new build is waiting and the user has not activated the refresh action
- **THEN** the current app session continues without an automatic reload

### Requirement: Connection-unavailable state is visible and disables network actions
The webapp SHALL show global connection-unavailable state and SHALL prevent network-required actions while the browser or backend connection is unavailable.

#### Scenario: Browser reports offline
- **WHEN** the browser reports that the app is offline
- **THEN** the app displays a compact global connection-unavailable banner below the topbar explaining that live updates and saving need the service

#### Scenario: Backend is unavailable
- **WHEN** the frontend app shell loads but required backend API requests fail
- **THEN** the app displays the global connection-unavailable banner and treats network-required actions as unavailable

#### Scenario: Connection-unavailable state affects update refresh
- **WHEN** the browser or backend connection is unavailable
- **THEN** the Updates refresh control is disabled and communicates that a connection is required

#### Scenario: Connection-unavailable state affects interest saves
- **WHEN** the browser or backend connection is unavailable
- **THEN** create, update, delete, and toggle interest actions are disabled or blocked before sending save requests

#### Scenario: Connection-unavailable state affects source image lookup
- **WHEN** the browser or backend connection is unavailable
- **THEN** automatic source image preview lookup is not requested and the editor communicates that preview requires a connection

### Requirement: Phone layout remains usable without replacing topbar
The webapp SHALL remain readable and operable on phone-width viewports while preserving the existing topbar navigation model.

#### Scenario: User views Updates on a phone
- **WHEN** the Updates view is displayed on a narrow viewport
- **THEN** update summary, controls, callouts, and update cards fit without horizontal overflow or overlapping text

#### Scenario: User manages interests on a phone
- **WHEN** the Manage interests view is displayed on a narrow viewport
- **THEN** form fields, source editor controls, and interest cards stack into a single-column layout with usable touch targets

#### Scenario: User opens installed app on iOS-style safe area
- **WHEN** the app is displayed in a standalone mobile viewport with safe-area insets
- **THEN** page content and global banners keep usable padding around device notches and home indicators
