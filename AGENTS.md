## Core Principles

- Prefer the smallest change that preserves existing architecture, public APIs, and
  behavior. For localized changes, avoid new modules, services, or broad
  refactors unless the existing structure cannot support the change cleanly.
- Use established project patterns for cross-cutting changes, public API changes,
  persistence changes, or new integrations. When a change affects these areas,
  explain the architectural trade-off before implementing or in the final summary.
- Do not add shortcuts, temporary workarounds, or quiet fallbacks. If a simple fix
  would bypass an existing boundary or hide a failure, use the boundary correctly
  instead.
- Ask for input before proceeding when the change alters public APIs, adds or
  removes a service or datastore, changes security-sensitive behavior, or requires
  choosing between two materially different architectures.

## Coding Guidelines

- Keep abstraction levels separated: orchestration coordinates work, adapters
  parse external formats, and shared helpers stay format-agnostic.
- Name functions with visible side effects using clear verbs that reveal the
  action at the call site, such as `raise`, `write`, `send`, or `delete`.
- Avoid default argument values for domain-specific collaborators or behavior.
  Defaults are mainly for small utility functions; application services should
  require their dependencies explicitly so missing wiring fails loudly.
- When rules seem to compete, apply them in this order: error handling boundaries,
  abstraction boundaries, explicit dependency wiring, naming clarity, then local
  style preferences.

### Error Handling

- Do not add defensive checks for internal invariants; let unexpected programmer
  errors fail loudly.
- At adapters, catch known I/O, network, and parsing failures only when converting
  them into domain-specific errors or use-case results.
- At orchestration boundaries, handle recoverable domain errors according to the
  use case. Let unexpected runtime errors flow to the highest-level handler.
- Any fallback that hides a failure from the user or caller must be explicit in
  the design and observable through logs, metrics, returned errors, or another
  diagnostic path.

## Verification & Commands

- The project uses Taskfile for running all common commands and verifications.
Run `task --list` to see various tasks.

- For code changes, add or update tests for new behavior when the project has a
  relevant test layer. Run the narrowest useful task during development and
  `task check` before finishing when feasible.

## Pull Requests

- After using the OpenSpec archive workflow to complete a change, open a PR for
  the completed change unless the user explicitly opts out.
- When opening a PR, include screenshots of any changed visual interface in the
  PR description.
- If screenshots cannot be produced locally, explain why in the PR description
  and include the best available substitute, such as a preview link or test
  evidence.
- If there are no visual changes, explicitly state that no screenshots are needed.

## Glossary

See .contextive/definitions.yml for project related terms.
