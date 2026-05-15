# Coding Rules

- Use `None` for missing scalar values. Empty strings are content, not absence.
- Keep abstraction levels separated: orchestration coordinates work, adapters parse external formats, and shared helpers stay format-agnostic.
