# 🏃 Running Tracker

A self-hosted app to **track, visualize, and analyze** your running
training. It pulls your runs and health data from **Garmin Connect** (and
optionally **Strava**), enriches every run with **accurate weather**, computes a
per-run **difficulty score**, surfaces **training-load and fitness trends**, and
can generate **AI coaching insights**. Designed to run as a Docker Compose stack
on a **Raspberry Pi 5 / OMV7** and be reached over the internet through a
**Cloudflare Tunnel**, with its own authentication and user database.

> Built around a real setup: Garmin Forerunner 245 → Garmin Connect, a Runna
> training plan, and a Strava subscription.

---

## What it does

- **Automatic data fetch** — a nightly worker (and an on-demand *Sync now*
  button) pulls activities plus sleep, HRV, resting HR, stress, body battery,
  steps and training readiness from Garmin. Strava is available as a secondary
  source.
- **Weather enrichment** — each run is matched to the temperature, "feels-like",
  humidity, wind and precipitation at its start time and location via
  [Open-Meteo](https://open-meteo.com) (free, no API key). Forecasts back the
  upcoming plan.
- **Difficulty scoring** — every run gets a 0–100 score blending intensity
  (HR), duration, elevation, heat, and your recovery state that day (sleep /
  body battery), with a breakdown that explains *why* it was hard.
- **Trends & analysis** — weekly volume, Acute:Chronic Workload Ratio (ACWR)
  with injury-risk zones, aerobic efficiency (pace-per-heartbeat), and a
  sleep-vs-performance view.
- **Training plan** — Runna plans arrive in Garmin/Strava; completed Runna runs
  are auto-tagged. Upcoming workouts can be entered manually or imported
  best-effort from a **Runna plan PDF**.
- **AI insights (pluggable)** — weekly summaries and single-run explanations via
  **Claude**, **OpenAI**, or a local **Ollama** model. Off until you configure a
  provider.
- **Auth & multi-user** — email/password accounts (argon2), JWT sessions. The
  first account becomes admin; registration can be locked afterward.
- **Secrets encrypted at rest** — your Garmin/Strava/LLM credentials are stored
  Fernet-encrypted, never in plaintext.

## Architecture

```
                    Cloudflare Tunnel
                           │
                    ┌──────▼──────┐
                    │  frontend   │  nginx: serves the React SPA
                    │  (nginx)    │  and proxies /api ─┐
                    └─────────────┘                    │ (single origin)
                    ┌─────────────┐   ┌────────────────▼─┐
                    │   worker    │   │     backend      │  FastAPI
                    │ APScheduler │   │  (uvicorn :8000) │
                    └──────┬──────┘   └────────┬─────────┘
                           │  nightly sync     │
                    ┌──────▼───────────────────▼─────────┐
                    │            db (PostgreSQL)          │
                    └────────────────────────────────────┘
   external: Garmin Connect · Strava API · Open-Meteo · LLM provider
```

- **Backend** — Python 3.12 / FastAPI / SQLAlchemy (async) / PostgreSQL.
- **Frontend** — React + TypeScript + Vite + Tailwind + Recharts (theme-aware,
  light/dark).
- **Worker** — APScheduler in its own container for the nightly sync + morning
  forecast refresh.
- All images build for **arm64** (Pi 5) and amd64.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a directory-level tour.

---

## Quick start (local)

```bash
git clone <this repo> && cd Runner
cp .env.example .env
./scripts/gen_keys.sh          # prints JWT_SECRET and ENCRYPTION_KEY — paste into .env
# set PUBLIC_BASE_URL=http://localhost (and TUNNEL_TOKEN can stay blank locally)

docker compose up -d --build db backend worker frontend
# open http://localhost  → register the first account (it becomes admin)
```

Want to explore the dashboards before connecting Garmin? Seed demo data:

```bash
docker compose exec backend python scripts/seed_demo.py
# then log in with demo@example.com / demopass123
```

Connect your real data: **Settings → Garmin Connect**, enter your Garmin email
and password (stored encrypted), then click **Sync now**.

---

## Deploy on a Raspberry Pi 5 (OMV7) with Cloudflare Tunnel

1. **Install Docker** on OMV7 (via the OMV-Extras "Compose" plugin, or
   `curl -fsSL https://get.docker.com | sh`). Put this repo in a shared folder,
   e.g. `/srv/dev-disk-by-uuid-XXXX/appdata/running-tracker`.

2. **Create the Cloudflare Tunnel.** In the
   [Zero Trust dashboard](https://one.dash.cloudflare.com) → **Networks →
   Tunnels → Create a tunnel** (choose *Cloudflared*). Add a **public hostname**
   (e.g. `tracker.yourdomain.com`) with service **`http://frontend:80`**. Copy
   the tunnel **token**.

3. **Configure `.env`:**
   ```bash
   cp .env.example .env
   ./scripts/gen_keys.sh   # paste JWT_SECRET + ENCRYPTION_KEY
   ```
   Set `PUBLIC_BASE_URL=https://tracker.yourdomain.com`, paste `TUNNEL_TOKEN`,
   and set a strong `POSTGRES_PASSWORD`.

4. **Launch:**
   ```bash
   docker compose up -d --build
   ```
   The `cloudflared` container dials out to Cloudflare — **no inbound ports** are
   opened on your router.

5. Visit your hostname, register your account, then **set
   `ALLOW_REGISTRATION=false`** in `.env` and `docker compose up -d backend` to
   lock down sign-ups.

> **Auth in front of the app:** for an extra layer you can also put a Cloudflare
> Access policy (email OTP / SSO) on the hostname in Zero Trust — the app's own
> login still applies underneath.

### How the tunnel is wired

The `cloudflared` container authenticates with the **tunnel token** from `.env`
and dials *outbound* to Cloudflare's edge — so nothing needs to be opened on your
router or OMV firewall. In the Zero Trust dashboard you map a **public hostname**
(e.g. `tracker.yourdomain.com`) to the internal service **`http://frontend:80`**;
Cloudflare terminates TLS at its edge and forwards requests down the tunnel to
that container. The app is single-origin (nginx serves the SPA *and* proxies
`/api`), so one hostname → one service is all you need.

If you'd rather manage the tunnel by config file than by dashboard token, you can
instead mount a `config.yml` + credentials JSON and change the `cloudflared`
command to `tunnel run <name>` — but the token method above needs no files.

### Local network access (via the Pi's IP)

Out of the box the `frontend` container also publishes a host port so you can
reach the app on your LAN without the tunnel — handy when you're home, and it
keeps working if the internet (or Cloudflare) is down:

```
http://<pi-ip>:8080          e.g. http://192.168.1.50:8080
```

- The port is set by **`WEB_PORT`** in `.env` (default `8080`). **Don't use 80 or
  443** — OMV's own web UI listens there.
- Same login, same data — it's the same containers, just reached directly instead
  of through Cloudflare. No CORS issues because the app is single-origin.
- Find the Pi's IP with `hostname -I` (or your router's DHCP list). On many
  networks `http://<hostname>.local:8080` works too via mDNS.
- **Two ways in at once:** LAN via `http://<pi-ip>:8080` *and* the internet via
  your Cloudflare hostname both work simultaneously — the tunnel reaches the
  container internally and doesn't care about the published port.
- One caveat: **connecting Strava** uses `PUBLIC_BASE_URL` for its OAuth redirect,
  so do that step from the Cloudflare hostname (Strava needs internet anyway).
  Garmin, weather, dashboards and everything else work fully over LAN.

> Want LAN-only, no internet exposure at all? Just leave `TUNNEL_TOKEN` blank and
> start without the tunnel:
> `docker compose up -d db backend worker frontend`.

---

## Integrations

| Source | How | Notes |
|--------|-----|-------|
| **Garmin** | `python-garminconnect` (unofficial) | Logs in with your Garmin credentials (encrypted at rest); caches refreshable tokens. Richest source: activities + sleep/HRV/steps/stress/body battery/readiness. |
| **Strava** | Official OAuth2 | Optional. Needs `STRAVA_CLIENT_ID/SECRET`. Personal-use only per Strava's API terms. |
| **Runna** | via Garmin/Strava + PDF | No public API. Completed Runna runs are auto-tagged; import the forward plan from a PDF or add it manually. |
| **Weather** | Open-Meteo | Free, keyless. Historical archive for past runs, forecast for the plan. |
| **LLM** | Claude / OpenAI / Gemini / Ollama | Pluggable; configured per-user in Settings or globally via env. |

**Heads-up on Garmin:** `python-garminconnect` is community-maintained and can
break temporarily if Garmin changes their login flow. It's isolated in
`backend/app/services/garmin.py` and surfaces a clear error on the Settings page
if that happens.

---

## Configuration reference

All settings live in `.env` (see `.env.example`). Required: `JWT_SECRET`,
`ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `PUBLIC_BASE_URL`, and `TUNNEL_TOKEN` (for
internet access). Everything else is optional.

- **`WEEK_STARTS_ON`** — `monday` (default, ISO / Runna weeks) or `sunday`. Controls
  the "This week" tile and the weekly-volume chart grouping. Only running activities
  count toward mileage (swims/rides are excluded).
- **LLM** — set `LLM_PROVIDER` to `anthropic`, `openai`, `gemini`, or `ollama` and the
  matching key (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY`), or configure
  it per-user in Settings. Gemini uses its OpenAI-compatible endpoint.

## Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///./dev.db" JWT_SECRET=dev \
       ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())')
uvicorn app.main:app --reload      # http://localhost:8000/api/docs
pytest                             # run the test suite

# Frontend (proxies /api to :8000)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

Schema is created automatically on startup (`Base.metadata.create_all`). For
evolving an existing database, Alembic is set up under `backend/alembic`.

## Security notes

- Passwords hashed with **argon2**; sessions are short-lived **JWTs**.
- Integration credentials and cached session tokens are **Fernet-encrypted** with
  `ENCRYPTION_KEY` — losing that key just means re-entering credentials.
- The stack exposes **no inbound ports**; all traffic arrives through the
  Cloudflare Tunnel over TLS.
- Keep `.env` out of git (it already is via `.gitignore`).

## Data & privacy

This is a personal, self-hosted app. Your Garmin/Strava/health data stays on your
Pi and is only sent to third parties you explicitly enable (Open-Meteo receives
run coordinates + timestamps for weather; your chosen LLM provider receives
aggregated stats when you request an insight — use Ollama to keep that local).

## License

MIT — see [LICENSE](LICENSE).
