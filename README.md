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
- Store interests in PostgreSQL relational tables.

- Enable/disable interests without deleting them.
- Provide a clear future prompt for evening briefings.

## Run it

Use the project task runner to start either the development or production Docker Compose stack.

Development mode keeps the Vite dev server available for local UI work:

```bash
task dev
```

Open:

```text
http://localhost:5173
```

Production mode builds the frontend once and serves the static app through nginx:

```bash
task prod
```

Open:

```text
http://localhost:8080
```

In both modes, the API is also exposed directly at:

```text
http://localhost:8765/api/health
```

To see all maintained project commands:

```bash
task --list
```

On the same computer, this works directly. For phone access, the computer and phone need to be on the same network and the servers would need to bind to a LAN-accessible address instead of `127.0.0.1`. That is intentionally not enabled by default for privacy/security.


## Codex environment

This repository includes project-scoped Codex configuration in `.codex/`:

- `.codex/config.toml` enables the `workspace-write` sandbox with network access so Codex can research technologies and install dependencies during development tasks.
- `.codex/setup.sh` prepares the toolchain used by the maintained Taskfiles: Python 3.14 through `uv`, Node.js when the base image does not already provide it, Task, and pnpm 11.1.2. It also installs backend and webapp dependencies so `task check` can run in the environment.

Use `.codex/setup.sh` as the setup script for the Codex environment.

## Backend stack

- FastAPI serves the JSON API and static UI.
- PostgreSQL stores interest data for the running app in relational tables.
- SQLModel/SQLAlchemy manage the backend database connection, schema initialization, and persistence rows.
- Pydantic validates and normalizes interest and source payloads.
- uv manages the Python environment and lockfile.
- Ruff enforces linting.
- mypy checks the typed backend modules in strict mode.

Common workflows live in `Taskfile.yml` so the README does not duplicate command strings.

## Persistence model

Interests are stored relationally instead of as a JSON document:

- `interests` stores interest rows keyed by `interest_id`.
- `interest_sources` stores source rows keyed by `source_id` and linked to interests.
- `source_ignore_keywords` stores ignore-keyword rows linked to sources.

The backend keeps the existing Pydantic domain models as the API boundary and uses infrastructure-only SQLModel rows to map those models into the relational schema. Legacy `backend/data/interests.json` data is not migrated automatically on app startup; run `uv run python scripts/migrate_interests_json_to_postgres.py` from `backend/` when you are ready to migrate it into the configured database. Add `--replace` only when you intentionally want to overwrite existing database interests.

## Docker Compose

The project has two explicit Compose files:

- `compose.dev.yaml` starts the backend plus the Vite dev server on `http://localhost:5173`.
- `compose.prod.yaml` builds the frontend for production and serves it through nginx on `http://localhost:8080`.

Useful commands:

```bash
task compose:dev:up      # development stack
task compose:prod:up     # production stack
task down                # stop both stacks
task compose:config      # validate both compose files
```

The backend API is exposed on `http://localhost:8765` in both modes. Compose also starts PostgreSQL and persists it in the `postgres-data` Docker volume. The legacy `./backend/data/interests.json` file is mounted read-only so you can run the migration script when you are ready.

## Cloud deployment

Render is the preferred first hosting target for this app because it can host the static frontend, Dockerized FastAPI backend, and managed Postgres database from one Blueprint. The repository includes `render.yaml` plus deployment notes in `docs/deployment/render.md`. Apply the Blueprint only after the production persistence path has moved from the local JSON file to Postgres.

## Privacy note

The interests database may reveal personal interests, professional priorities, people you follow, and private learning goals. Keep database backups and exported data private unless you intentionally decide to sync or publish them.

## How Hermes can use it

Ask Hermes:

```text
Read my Learning Engine interests from the Learning Engine API or PostgreSQL database and prepare an evening briefing.
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
├── render.yaml            # Render Blueprint for the hosted stack
├── compose.dev.yaml       # Docker Compose development stack
├── compose.prod.yaml      # Docker Compose production stack
├── docs/deployment/       # cloud deployment notes
├── backend/
│   ├── pyproject.toml     # uv project config, dependencies, ruff, mypy, pytest
│   ├── data/              # legacy JSON seed available to the migration script
│   ├── learning_engine/   # typed FastAPI backend package
│   ├── scripts/           # backend/API utility scripts
│   └── tests/             # backend tests
├── webapp/                # frontend app
└── briefings/             # generated briefing artifacts
```

## Design principle

Clean SaaS shell, personal learning soul. Keep the UI quiet, useful, local-first, and free of unnecessary decoration.
