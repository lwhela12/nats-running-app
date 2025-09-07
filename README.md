# Nat's Running App (MVP)

Monorepo for the MVP: chat onboarding, feasibility, plan generation, calendar, logging, and simple adaptation rules.

Refer to `Docs/` for product/design. See `apps/api` for FastAPI backend.

## Local Dev (Backend)

1) Create `.env` in `apps/api` (see `Docs/agents.md` for variables):

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nra
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-secret-change-me
ACCESS_TOKEN_TTL=900
REFRESH_TOKEN_TTL=1209600
ALLOWED_ORIGINS=http://localhost:3000
RIEGEL_K=1.06
WEEKLY_VOLUME_CAP=0.10
```

2) Python env and install:

```
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

3) Start Postgres & Redis (optional, via Docker):

```
docker compose -f ops/docker/compose.yml up -d
```

4) Run DB migrations:

```
alembic -c ops/migrations/alembic.ini upgrade head
```

5) Run API:

```
uvicorn app.main:app --reload
```

OpenAPI: http://localhost:8000/docs

## Local Dev (Frontend)

1) Set API base in `apps/web/.env.local`:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

2) Install and run:

```
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000

Login or Register, then complete the onboarding flow.

## One-command Dev

From the repo root, you can bring up Postgres/Redis, run the API (with migrations), and start the Next.js dev server together:

```
npm install
npm run dev
```

What it does:
- `docker compose -f ops/docker/compose.yml up -d`
- Sets up Python venv, installs API deps, runs Alembic migrations
- Starts `uvicorn` on `:8000` and Next.js on `:3000` concurrently

Requirements:
- Docker running locally
- Python 3.11+
- Node 18+

## Repo Layout

- `apps/web` — Next.js app (to be added)
- `apps/api` — FastAPI backend
- `packages/schemas` — Generated TS types from OpenAPI
- `ops/migrations` — Alembic migrations
- `ops/docker` — Local dev containers

## Tests

```
cd apps/api
pytest -q
```
