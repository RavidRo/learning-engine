# Render Deployment

This repository includes a Render Blueprint at the repository root:

```text
render.yaml
```

Use the Blueprint after the app's persistence layer has been migrated from the
local JSON file to Postgres. The Blueprint already provisions a Render Postgres
database and exposes its connection string to the backend as `DATABASE_URL`, but
the current backend code does not consume that variable yet.

## Target architecture

The Blueprint creates three Render resources:

1. `learning-engine-frontend` — a free static site built from `webapp/`.
2. `learning-engine-backend` — a Docker web service built from `backend/`.
3. `learning-engine-db` — a managed Render Postgres database on Render's free plan.

The backend Docker service sets `rootDir: backend`, then uses `./Dockerfile` and
`.` for the Dockerfile path and context so Render resolves both paths inside
`backend/`.

The static frontend keeps browser API calls same-origin by rewriting `/api` and
`/api/*` requests to the backend service's public Render URL. This avoids adding
cross-origin browser API configuration while preserving the local development
shape where frontend code calls relative `/api` paths.

## Region and expected starter cost

The backend service and Postgres database are configured for Render's
`frankfurt` region because Frankfurt is the closest available Render
service/datastore region to Israel. Render static sites do not require a region
choice because they are served through Render's global CDN.

At the time this deployment plan was written, the intended starter setup was:

- Static frontend: free.
- Backend web service: Render `starter` plan.
- Postgres: Render `free` plan.

Confirm the final monthly price and free database limitations in the Render
Dashboard before applying the Blueprint because Render pricing, plan names, and
account-level included usage can change.

## Apply the Blueprint

1. Push this repository to the Git provider connected to your Render account.
2. In Render, create a new Blueprint and select this repository.
3. Review the resources from `render.yaml` before confirming creation.
4. Fill optional secrets when prompted:
   - `X_BEARER_TOKEN`, if X/Twitter collection should be enabled.
   - `SPOTIFY_ACCESS_TOKEN`, if Spotify collection should be enabled.
5. Create the Blueprint resources.
6. Wait for the database, backend, and frontend deploys to finish.
7. Open the frontend `onrender.com` URL and confirm `/api/health` works through the frontend domain.

## Post-create checks

After Render creates the services, verify these settings in the dashboard:

- The backend service uses `rootDir=backend`, `dockerfilePath=./Dockerfile`, and
  `dockerContext=.` so Render does not look for `backend/backend`.
- The backend service has `PORT=8765` because the existing backend Dockerfile
  starts uvicorn on port `8765`.
- The backend service and Postgres database are both in the `frankfurt` region.
- The backend service has `DATABASE_URL` populated from `learning-engine-db`.
- The frontend static site uses `pnpm install --frozen-lockfile && pnpm run
  build`; do not run `corepack enable` in the Render static-site build image
  because `/usr/bin/pnpm` can be read-only.
- The frontend static site publishes `./dist` from `rootDir=webapp`.
- The frontend static site has rewrite rules for `/api/*`, `/api`, and `/*`.
- The `/api/*` and `/api` rewrite destinations match the actual backend public
  URL. If Render assigns a different backend URL than
  `https://learning-engine-backend.onrender.com`, update both rewrite
  destinations to the actual URL.

## Persistence migration note

Do not rely on the hosted backend for durable data until the Postgres-backed
repository implementation is complete. Render service filesystems are not the
same persistence boundary as the local `backend/data/interests.json` workflow.
The Postgres migration should make `DATABASE_URL` the explicit production
persistence dependency and should fail loudly if required production database
configuration is missing.

## Custom domain

The initial deployment can use Render's generated `onrender.com` domains. Add a
custom domain later after the first deployment is healthy and the frontend API
rewrites have been verified.
