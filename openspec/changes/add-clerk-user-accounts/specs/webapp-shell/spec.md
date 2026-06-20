## ADDED Requirements

### Requirement: Webapp initializes Clerk authentication
The webapp SHALL initialize Clerk at the app entry point and make Clerk session state available to the app shell.

#### Scenario: Clerk publishable key is configured
- **WHEN** the webapp loads with Clerk configuration available
- **THEN** the app shell can render signed-in, signed-out, and user controls from Clerk state

#### Scenario: Clerk publishable key is missing
- **WHEN** the webapp loads without required Clerk frontend configuration
- **THEN** the app reports a clear configuration error instead of silently loading unauthenticated data views

### Requirement: Signed-out users see authentication controls
The webapp SHALL show clear sign-in and sign-up controls when the viewer is signed out.

#### Scenario: User is signed out
- **WHEN** a signed-out user opens the app
- **THEN** the app shell shows sign-in and sign-up actions and does not request user data APIs

#### Scenario: User signs in
- **WHEN** the user completes sign-in
- **THEN** the app shell loads user data views for the signed-in user

### Requirement: Signed-in user is required in the shell
The webapp SHALL require a signed-in Clerk user before user data views are loaded.

#### Scenario: User is signed in
- **WHEN** a signed-in user opens the app
- **THEN** the app shell loads user data views for that user

#### Scenario: User signs out
- **WHEN** the current user signs out
- **THEN** the app clears user data views and returns to signed-out authentication controls

#### Scenario: Session changes
- **WHEN** the active Clerk session changes to a different user
- **THEN** the app invalidates user data queries and reloads data for the signed-in user

### Requirement: API requests include Clerk session token
The webapp SHALL attach a Clerk session bearer token to backend API requests that access user data.

#### Scenario: User API request is sent
- **WHEN** the app requests interests, updates, collections, interest import, interest export, or collection writes
- **THEN** the request includes the current Clerk session token in the `Authorization` header

#### Scenario: Session token is unavailable
- **WHEN** the app cannot obtain a Clerk session token
- **THEN** it does not send user data API requests and presents an authentication-required state

### Requirement: Users can retrieve an MCP token
The webapp SHALL let signed-in users retrieve a current Clerk session token for configuring MCP clients.

#### Scenario: Signed-in user opens MCP setup
- **WHEN** a signed-in user opens account controls
- **THEN** the account controls provide an MCP setup surface that explains the token is used as the MCP bearer token

#### Scenario: User copies MCP token
- **WHEN** a signed-in user requests their MCP token from the MCP setup surface
- **THEN** the webapp retrieves the current Clerk session token and makes it available for copying without storing it in application data

#### Scenario: User configures Codex MCP
- **WHEN** a signed-in user views the MCP setup surface
- **THEN** the webapp shows the `/mcp` endpoint and Codex configuration command pattern that uses the copied token through an environment variable
