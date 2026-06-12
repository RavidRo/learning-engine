# Coding Guidelines

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

## Error Handling

- Do not add defensive checks for internal invariants; let unexpected programmer
  errors fail loudly.
- At adapters, catch known I/O, network, and parsing failures only when converting
  them into domain-specific errors or use-case results.
- At orchestration boundaries, handle recoverable domain errors according to the
  use case. Let unexpected runtime errors flow to the highest-level handler.
- Any fallback that hides a failure from the user or caller must be explicit in
  the design and observable through logs, metrics, returned errors, or another
  diagnostic path.