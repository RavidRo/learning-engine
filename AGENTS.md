## Core Principles

- **Bias towards tasteful simplicity** - favor elegant, readable, maintainable solutions that add minimal complexity. Avoid over-engineering, premature optimization, and defensive coding patterns that obscure intent.
- **Always implement proper, architectural solutions** - no shortcuts, hacky fixes, or temporary workarounds. Research best practices when needed.
- **Prefer optimistic code over defensive code** - let errors surface loudly during development rather than wrapping everything in if-checks and try/catch blocks. Handle errors architecturally at higher levels (e.g., error handling middleware).
- **Question and recommend alternatives** - your goal is better outcomes, not blind execution. Stop and ask for input when appropriate.

## Coding Guidelines

- Keep abstraction levels separated: orchestration coordinates work, adapters parse external formats, and shared helpers stay format-agnostic.
- Name functions with visible side effects using clear verbs that reveal the action at the call site, such as `raise`, `write`, `send`, or `delete`.

### Error Handling

- Prefer handling recoverable errors at the consuming boundary so each use case can choose how to handle it. Shared lower-level functions should classify and raise domain errors instead of deciding the fallback behavior for every caller.
- Do not introduce quiet fallbacks. Any fallback that hides a failure from the user or caller must be explicit in the design and observable through logs, metrics, or another diagnostic path.
- Keep `try`/`except`/`catch` clauses narrow and semantically meaningful: convert known boundary failures into domain-specific exceptions close to the adapter, and let unexpected exceptions flow to a single higher-level handler with logging.

## Verification & Commands

The project uses Taskfile for running all common commands and verifications.
Run `task --list` to see various tasks.

## Pull Requests

- After archiving an OpenSpec change, open a PR for the completed change unless the user explicitly opts out.
- When opening a PR, include screenshots of any changed visual interface in the PR description.
- If there are no visual changes, explicitly state that no screenshots are needed.

## Glossary

See .contextive/definitions.yml for project related terms.
