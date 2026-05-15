## TypeScript & Code Style

- Never use `any` in TypeScript
- Prefer `type` over `interface`
- Prefer arrow functions over `function` keyword
- Prefer `const` over `let` - create helper functions with early return instead of setting `let` variables inside conditionals
- Use camelCase for const and variable names
- Prefer early return over long if statements and nested code
- Use direct imports: `useEffect` not `React.useEffect`
- Prefer top-level imports over inline/dynamic imports (`await import(...)`) when no circular dependency exists
- Prefer async/await over .then/.catch
- Add JSDoc comments to new utility functions
- Only comment non-obvious code - avoid useless comments like "// Save data collection mutation" before `saveDataCollection()`
- Loosely prefer one React component per file

## React Patterns

- Use `useReducer` when a component needs 3+ `useState` hooks
- Abstract state/logic into `use[Component]State()` hooks to separate computation from display logic and enable unit testing

### `useEffect` Discipline

**Treat every `useEffect` as a code smell until proven necessary.** Before writing or reviewing a `useEffect`, consult <https://react.dev/learn/you-might-not-need-an-effect> and verify it doesn't match a known anti-pattern.

**Never use `useEffect` for:**

- **Deriving state from props/state** — compute during render: `const x = derive(props)` or use `useMemo`
- **Syncing props into state** — use the prop directly, or use a ref to detect prop changes during render
- **Notifying parents of state changes** — call the callback in the event handler that caused the change
- **Resetting state when a prop changes** — use a `key` prop on the component, or a `useState` lazy initializer
- **One-time initialization from already-available data** — use `useState(() => computeInitial())` lazy initializer
- **Navigation side effects** — return `<Navigate replace />` in JSX
- **Assigning to refs** — assign `ref.current` directly in the render body

**Prefer these hooks over `useEffect` when applicable:**

- `useSyncExternalStore` — for subscribing to external stores, browser APIs (`matchMedia`, `addEventListener`)
- `useEffectEvent` — to extract handler logic out of effects, eliminating stale closures and dependency bloat
- `useOptimistic` + `useTransition` — for optimistic UI updates instead of `useState` + `useEffect` + `useMutation`
- `useTransition` — for wrapping async operations with automatic `isPending` instead of manual loading state
- `useDeferredValue` — for deferring expensive re-renders instead of timer-based debounce

**Legitimate `useEffect` uses** (keep these): DOM event listeners with cleanup, external system subscriptions (WebSocket, SDK listeners), DOM measurements/scroll, timers with cleanup, analytics/tracking, async operations on mount.
