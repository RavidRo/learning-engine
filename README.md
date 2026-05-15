# Learning Engine Starter

A tiny local-first starter project for Ravid's custom learning engine.

The first goal is intentionally small: maintain a personal list of technology interests that Hermes can later read and use to prepare an evening briefing.

## What it does now

- Clean Linear-inspired responsive web UI for phone and computer.
- Add technology interests. Other interest types are intentionally excluded for now and will be added incrementally.
- Technology interests can include an official website URL, official RSS/Atom feed URL, watch keywords, and ignore keywords.
- Check enabled technology feeds for matching updates from the local UI.
- Show active/tracked/feed counts in a small local summary panel.
- Store interests in a local JSON file:

```text
data/interests.json
```

- Enable/disable interests without deleting them.
- Provide a clear future prompt for evening briefings.

## Run it

From this folder:

```bash
uv run python server.py
```

Open:

```text
http://localhost:8765
```

You can also run the app directly through Uvicorn:

```bash
uv run uvicorn learning_engine.app:app --host 127.0.0.1 --port 8765
```

On the same computer, this works directly. For phone access, the computer and phone need to be on the same network and the server would need to bind to a LAN-accessible address instead of `127.0.0.1`. That is intentionally not enabled by default for privacy/security.

## Backend stack

- FastAPI serves the JSON API and static UI.
- Pydantic validates and normalizes technology interest payloads.
- uv manages the Python environment and lockfile.
- Ruff enforces linting.
- mypy checks the typed backend modules in strict mode.

Useful development commands:

```bash
uv run ruff check .
uv run mypy
uv run pytest -s
```

## Privacy note

The interests file may eventually reveal personal interests, professional priorities, people you follow, and private learning goals. Keep it local unless you intentionally decide to sync or publish it.

## How Hermes can use it

Ask Hermes:

```text
Read my Learning Engine interests from ~/projects/learning-engine-starter/data/interests.json and prepare an evening briefing.
```

For now, Hermes will use the technology interests as context. Later versions can add more interest types such as people, newsletters, blogs, podcasts, and companies.

## Technology interests

Technology is the first type-specific interest workflow. For example, TypeScript is tracked with:

```text
Official site: https://www.typescriptlang.org/
Official feed: https://devblogs.microsoft.com/typescript/feed/
```

Use watch keywords for signal such as `release`, `beta`, `rc`, `compiler`, and `breaking change`. Use ignore keywords for noise such as `webinar` or `case study`. There is no generic "sources to watch" field: sources are inferred from the interest type and represented as official technology URLs/feeds.

## Suggested next features

1. Add source adapters for technology interests: GitHub releases, changelog pages, npm/package releases.
2. Add "briefing preferences" such as length, tone, novelty threshold, and technical depth.
3. Add active learning cards from briefings.
4. Add topic roadmaps and spaced repetition.
5. Add the next interest type only after technology feels useful.
6. Add a daily/weekly archive of generated briefings.

## Project structure

```text
learning-engine-starter/
├── pyproject.toml         # uv project config, dependencies, ruff, mypy, pytest
├── server.py              # compatibility entrypoint for the FastAPI app
├── learning_engine/       # typed FastAPI backend package
│   ├── app.py             # app factory, routes, static-file mounting
│   ├── collector.py       # feed/page parsing and update collection
│   ├── fetching.py        # network fetch primitive
│   ├── models.py          # Pydantic schemas
│   └── storage.py         # JSON-backed interest persistence
├── data/
│   └── interests.json     # Hermes-readable interest store
├── public/
│   ├── index.html         # responsive UI
│   ├── styles.css         # visual design
│   └── app.js             # client-side app logic
└── tests/
    └── test_server.py     # feed parsing + technology update tests
```

## Design principle

Clean SaaS shell, personal learning soul. Keep the UI quiet, useful, local-first, and free of unnecessary decoration.
