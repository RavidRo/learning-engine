## Core Principles

- **Bias towards tasteful simplicity** - favor elegant, readable, maintainable solutions that add minimal complexity. Avoid over-engineering, premature optimization, and defensive coding patterns that obscure intent.
- **Always implement proper, architectural solutions** - no shortcuts, hacky fixes, or temporary workarounds. Research best practices when needed.
- **Prefer optimistic code over defensive code** - let errors surface loudly during development rather than wrapping everything in if-checks and try/catch blocks. Handle errors architecturally at higher levels (e.g., error handling middleware).
- **Question and recommend alternatives** - your goal is better outcomes, not blind execution. Stop and ask for input when appropriate.

## Coding Guidelines

- Keep abstraction levels separated: orchestration coordinates work, adapters parse external formats, and shared helpers stay format-agnostic.

## Verification & Commands

The project uses Taskfile for running all common commands and verifications.
Run `task --list` to see various tasks.

## Pull Requests

- When opening a PR, include screenshots of any changed visual interface in the PR description.
- If there are no visual changes, explicitly state that no screenshots are needed.

## Glossary

See .contextive/definitions.yml for project related terms.
