# Learning Engine

A local-first project for Ravid's custom learning engine.

The first goal is intentionally small: maintain a personal list of interests and sources that Hermes can later read and use to prepare an evening briefing.

## What it does now

- Clean Linear-inspired responsive web UI for phone and computer.
- Add general interests such as people, organizations, subjects, and specific technologies.
- Describe what information about each interest belongs in final briefings.
- Attach feed or page sources to interests.
- Check enabled sources for updates from the local UI.
- Show active/tracked/source counts in a small local summary panel.
- Store interests in a local JSON file:

```text
backend/data/interests.json
```

- Enable/disable interests without deleting them.
- Provide a clear future prompt for evening briefings.

## Run it

Use the project task runner:

```bash
task dev
```

Open:

```text
http://localhost:8765
```

To see all maintained project commands:

```bash
task --list
```

On the same computer, this works directly. For phone access, the computer and phone need to be on the same network and the server would need to bind to a LAN-accessible address instead of `127.0.0.1`. That is intentionally not enabled by default for privacy/security.

## Backend stack

- FastAPI serves the JSON API and static UI.
- Pydantic validates and normalizes interest and source payloads.
- uv manages the Python environment and lockfile.
- Ruff enforces linting.
- mypy checks the typed backend modules in strict mode.

Common workflows live in `Taskfile.yml` so the README does not duplicate command strings.

## Docker Compose

Run both services with:

```bash
task compose:up
```

The backend is exposed on `http://localhost:8765`, the frontend on `http://localhost:5173`, and backend data is mounted at `./backend/data`.

## Privacy note

The interests file may eventually reveal personal interests, professional priorities, people you follow, and private learning goals. Keep it local unless you intentionally decide to sync or publish it.

## How Hermes can use it

Ask Hermes:

```text
Read my Learning Engine interests from ~/projects/learning-engine/backend/data/interests.json and prepare an evening briefing.
```

Hermes can use interests as briefing context and sources as the raw material for update collection.

## Interests and sources

An interest is a general topic. It can be a person, organization, subject, specific technology, or anything else worth tracking. For example, TypeScript can be tracked with:

```text
Description: Track language/compiler updates and important release announcements.
Source: Official site, page, https://www.typescriptlang.org/
Source: TypeScript dev blog, feed, https://devblogs.microsoft.com/typescript/feed/
```

The first source adapters support RSS/Atom feeds and best-effort web pages. Platform-specific sources such as YouTube channels or Twitter/X accounts should become first-class source types after dedicated adapters exist.

## Suggested next features

1. Add source adapters for YouTube channels, Twitter/X accounts, GitHub releases, changelog pages, npm/package releases.
2. Add "briefing preferences" such as length, tone, novelty threshold, and technical depth.
3. Add active learning cards from briefings.
4. Add topic roadmaps and spaced repetition.
5. Add source-level controls when collection adapters need them.
6. Add a daily/weekly archive of generated briefings.

## Project structure

```text
learning-engine/
├── Taskfile.yml           # maintained local development commands
├── backend/
│   ├── pyproject.toml     # uv project config, dependencies, ruff, mypy, pytest
│   ├── server.py          # compatibility entrypoint for the FastAPI app
│   ├── data/              # Hermes-readable interest store
│   ├── learning_engine/   # typed FastAPI backend package
│   ├── scripts/           # backend/API utility scripts
│   └── tests/             # backend tests
├── webapp/                # frontend app
└── briefings/             # generated briefing artifacts
```

## Design principle

Clean SaaS shell, personal learning soul. Keep the UI quiet, useful, local-first, and free of unnecessary decoration.
