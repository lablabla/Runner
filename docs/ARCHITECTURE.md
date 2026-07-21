# Architecture

A directory-level tour of the codebase.

## Repository layout

```
Runner/
├── docker-compose.yml        # db · backend · worker · frontend · cloudflared
├── .env.example              # all configuration (copy to .env)
├── scripts/gen_keys.sh       # generate JWT_SECRET + ENCRYPTION_KEY
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, router wiring, create_all on boot
│   │   ├── config.py         # pydantic-settings (env)
│   │   ├── database.py       # async SQLAlchemy engine/session + Base
│   │   ├── core/
│   │   │   ├── security.py    # argon2 hashing + JWT
│   │   │   └── crypto.py      # Fernet encryption for stored credentials
│   │   ├── models/           # SQLAlchemy tables
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── api/
│   │   │   ├── deps.py        # get_current_user (JWT)
│   │   │   └── routes/        # auth, integrations, activities, metrics,
│   │   │                      #   plan, analysis, sync
│   │   ├── services/
│   │   │   ├── garmin.py      # unofficial Garmin client wrapper
│   │   │   ├── strava.py      # Strava OAuth2 + fetch
│   │   │   ├── weather.py     # Open-Meteo enrichment
│   │   │   ├── normalize.py   # provider payload → common activity shape
│   │   │   ├── difficulty.py  # per-run 0–100 difficulty score
│   │   │   ├── trends.py      # weekly load, ACWR, efficiency (pandas)
│   │   │   ├── runna.py       # Runna tag detection + PDF plan parsing
│   │   │   └── sync.py        # per-user sync orchestrator
│   │   ├── llm/              # pluggable providers (anthropic/openai/ollama)
│   │   └── worker/scheduler.py # APScheduler nightly sync
│   ├── scripts/seed_demo.py  # synthetic data for exploring the UI
│   ├── tests/                # pytest: crypto, difficulty, trends, auth
│   └── alembic/              # migrations (create_all covers first boot)
└── frontend/
    ├── src/
    │   ├── api/              # typed client + TanStack Query hooks
    │   ├── components/       # Layout, ui primitives, charts (Recharts)
    │   ├── pages/            # Login, Dashboard, Activities, Trends, Plan,
    │   │                     #   Insights, Settings
    │   ├── palette.ts        # validated light/dark chart palette
    │   ├── auth.tsx / theme.tsx
    │   └── App.tsx           # routes + auth guard
    └── nginx.conf            # serves SPA + proxies /api to backend
```

## Request flow

1. Browser → Cloudflare Tunnel → `frontend` (nginx).
2. nginx serves the SPA; `/api/*` is proxied to `backend:8000` (same origin, no
   CORS in production).
3. Backend authenticates the JWT, reads/writes PostgreSQL, and calls external
   services (Garmin/Strava/Open-Meteo/LLM) as needed.

## Sync pipeline (`services/sync.py`)

```
for each user:
  garmin: fetch activities since backfill window → normalize → upsert
          fetch daily wellness (sleep/HRV/steps/…) → upsert daily_metrics
  strava: fetch activities after window → normalize → upsert (skip Garmin dupes)
  enrich: for each activity without weather → Open-Meteo at start point/time
  score:  compute difficulty from HR/duration/elevation/heat/readiness
```

Triggered on demand via `POST /api/sync` and nightly by the worker.

## Data model

`users` ← `integration_credentials` (encrypted), `activities` (← `weather`),
`daily_metrics`, `planned_workouts`, `insights`. Uniqueness on
`(user, source, source_id)` for activities and `(user, date)` for daily metrics
keeps syncs idempotent.

## Key design choices

- **Garmin credentials tied to app auth, encrypted at rest** — entered after
  login on the Settings page; the raw password is exchanged for refreshable
  tokens, both stored Fernet-encrypted.
- **Single origin** — nginx fronts both SPA and API so the browser, Cloudflare,
  and cookies all see one host.
- **Provider isolation** — anything that can break externally (Garmin auth,
  Strava, weather, LLM) lives behind a single service module with graceful
  degradation.
- **Pluggable LLM** — `llm/factory.py` selects Claude/OpenAI/Ollama from
  per-user config or env; analysis is entirely optional.
