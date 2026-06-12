# Render Deployment

This repository uses Render as a cloud provider for deploying the app without managing a server directly. Configurations are described in a blueprint:

```text
render.yaml
```

## Target architecture

The Blueprint creates three Render resources:

1. `learning-engine-frontend` — a free static site built from `webapp/`.
2. `learning-engine-backend` — a Docker web service built from `backend/`.
3. `learning-engine-db` — a managed Render Postgres database on Render's free plan.

## Region

The backend service and Postgres database are configured for Render's
`frankfurt` region because Frankfurt is the closest available Render
service/datastore region to Israel.

## Deployment

Render is synced to the main branch, commit/merger to `main` in order to deploy changes.
