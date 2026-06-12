## Core Principles

- Use established project patterns for cross-cutting changes, public API changes,
  persistence changes, or new integrations. When a change affects these areas,
  explain the architectural trade-off before implementing or in the final summary.
- Do not add shortcuts, temporary workarounds, or quiet fallbacks. If a simple fix
  would bypass an existing boundary or hide a failure, use the boundary correctly
  instead.
- Ask for input before proceeding when the change alters public APIs, adds or
  removes a service or datastore, changes security-sensitive behavior, or requires
  choosing between two materially different architectures.


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

## More details

- For project related terms, see `.contextive/definitions.yml` .
- For coding guidelines, see `./docs/coding_guidelines.md` .
- For deployment details, see `./docs/deployment.md` .
