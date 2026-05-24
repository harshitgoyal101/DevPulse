# DevPulse — Windows setup (no Docker)

This guide installs and runs DevPulse on **Windows 10/11** with **PostgreSQL**, **Redis**, **Python**, and **Node** installed locally. It does not use Docker.

For the full API reference, architecture, and feature list, see [README.md](README.md).

---

## What you will run


| Process              | Purpose                           | Default URL / port                             |
| -------------------- | --------------------------------- | ---------------------------------------------- |
| PostgreSQL           | Database                          | `localhost:5432`                               |
| Redis                | Celery message broker             | `localhost:6379`                               |
| Django (`runserver`) | REST API                          | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| Celery worker        | Webhook → `BuildEvent` processing | (no HTTP port)                                 |
| Vite (`npm run dev`) | React UI (optional)               | [http://localhost:5173](http://localhost:5173) |


You need **three terminals** for day-to-day development (API, Celery, frontend). Postgres and Redis run as Windows services or background processes.

---

## 1. Prerequisites

Install these before cloning or continuing:


| Tool           | Version | Install options                                                                                                        |
| -------------- | ------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Python**     | 3.12+   | [python.org](https://www.python.org/downloads/windows/) — check **“Add python.exe to PATH”** during setup              |
| **Node.js**    | 18+     | [nodejs.org](https://nodejs.org/) LTS installer                                                                        |
| **PostgreSQL** | 16      | [PostgreSQL Windows installer](https://www.postgresql.org/download/windows/) — remember the superuser password you set |
| **Redis**      | 7       | See [Redis on Windows](#redis-on-windows) below                                                                        |
| **Git**        | any     | [git-scm.com](https://git-scm.com/download/win) (optional, for clone)                                                  |


Verify in **PowerShell** or **Command Prompt**:

```powershell
python --version
node --version
psql --version
```

If `python` is missing but `py` works, use `py -3.12` instead of `python` in the steps below.

---

## 2. Redis on Windows

Redis does not ship an official native Windows build. Pick **one** option:

### Option A — Memurai (recommended, native Windows)

[Memurai](https://www.memurai.com/) is Redis-compatible and runs as a Windows service.

1. Download and install **Memurai Developer** (free for development).
2. Ensure the service is running (default port **6379**).
3. Test:

```powershell
# If memurai-cli is on PATH:
memurai-cli ping
# Expected: PONG
```

Use the same URLs in `.env` as for Redis: `redis://localhost:6379/0`.

### Option B — Redis via Chocolatey

```powershell
choco install redis-64 -y
redis-server
```

Leave that window open, or install Redis as a Windows service per the package docs.

### Option C — WSL2 only for Redis (hybrid)

If you use WSL2 but want Django on Windows:

```bash
# Inside WSL (Ubuntu)
sudo apt update && sudo apt install -y redis-server
sudo service redis-server start
redis-cli ping
```

From Windows, `localhost:6379` usually forwards to WSL Redis. If connection fails, use the WSL IP from `hostname -I` in `.env` instead of `localhost`.

---

## 3. PostgreSQL database

1. Open **pgAdmin** or **SQL Shell (psql)** from the Start menu.
2. Create a user and database matching `.env.example`:

```sql
CREATE USER devpulse WITH PASSWORD 'devpulse';
CREATE DATABASE devpulse OWNER devpulse;
GRANT ALL PRIVILEGES ON DATABASE devpulse TO devpulse;
```

1. Confirm connectivity:

```powershell
psql -U devpulse -d devpulse -h localhost -c "SELECT 1;"
```

If `psql` is not on PATH, use the full path, e.g. `"C:\Program Files\PostgreSQL\16\bin\psql.exe"`.

---

## 4. Clone and configure environment

```powershell
cd $HOME\Desktop
git clone <your-repo-url> DevPulse
cd DevPulse
```

Copy environment file at the **repository root** (same folder as `docker-compose.yml`):

```powershell
copy .env.example .env
```

Edit `.env` in Notepad or your editor. Minimum for local dev:

```ini
DJANGO_SECRET_KEY=change-me-to-a-long-random-string
DJANGO_DEBUG=True
DATABASE_URL=postgres://devpulse:devpulse@localhost:5432/devpulse
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
WEBHOOK_BASE_URL=http://127.0.0.1:8000
```

`DATABASE_URL` must use the `postgres://` scheme (not `postgresql://` alone if your client differs — the app expects `postgres://` per project settings).

---

## 5. Backend (Python)

### 5.1 Virtual environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

**Command Prompt** alternative:

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
```

### 5.2 Install dependencies

```powershell
pip install -e ".[dev]"
```

### 5.3 Database migrations and demo data

Still in `backend` with the venv activated:

```powershell
python manage.py migrate
python manage.py load_demo_seed
```

Demo login (after seed): `**alice@acme.dev**` / `**demo-password123**`.

Optional superuser:

```powershell
python manage.py createsuperuser
```

Use **email** when prompted (no username field).

---

## 6. Run the stack (three terminals)

Keep PostgreSQL and Redis running first. Activate the venv (`.\.venv\Scripts\Activate.ps1`) in each backend terminal.

### Terminal 1 — API

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

- API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Terminal 2 — Celery worker

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info
```

Wait until you see `celery@... ready`. If you see **Connection refused** on port 6379, Redis is not running — go back to [Redis on Windows](#redis-on-windows).

### Terminal 3 — Frontend (optional)

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — Vite proxies `/api` to Django.

---

## 7. Smoke test (webhook pipeline)

With API and Celery running:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py simulate_webhook --org-slug acme --project-slug web-api
```

Expected: `**Response: 202 Accepted**`, and in the Celery terminal a line like `Task apps.ingestion.tasks.process_webhook_delivery[...] succeeded`.

Check data in admin → **Build events**, or:

```powershell
python manage.py shell -c "from apps.ingestion.models import BuildEvent; print(BuildEvent.objects.order_by('-created_at').values('status','duration','branch')[:3])"
```

---

## 8. Running tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

Tests use SQLite in memory — no Postgres/Redis required for `pytest`.

---

## Troubleshooting

### `Connection refused` on `localhost:6379` (Celery)

- Redis/Memurai is not started. Start the service or run `redis-server` / Memurai.
- Confirm: `memurai-cli ping` or `redis-cli ping` → `PONG`.

### `ImproperlyConfigured: Set DATABASE_URL`

- Create `.env` in the **repo root**, not only under `backend/`.
- Restart the terminal after editing `.env`.

### `password authentication failed for user "devpulse"`

- Recreate the Postgres user/database (step 3) or fix `DATABASE_URL` to match your credentials.

### `psql` / `python` not recognized

- Reinstall with “Add to PATH”, or use full paths to `psql.exe` and `python.exe`.
- Try the `**py`** launcher: `py -3.12 -m venv .venv`

### Webhook returns 202 but no `BuildEvent`

- Celery worker must be running in a **second** terminal.
- Check the worker log for errors; fix Redis connectivity first.

### `simulate_webhook`: Project not found

- Run `python manage.py load_demo_seed` first.
- Org slug in seed is `**acme`**, project `**web-api**`:  
`--org-slug acme --project-slug web-api`

### PowerShell cannot run scripts (venv activate)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Quick reference


| Task         | Command (from `backend`, venv on)                                          |
| ------------ | -------------------------------------------------------------------------- |
| Migrate      | `python manage.py migrate`                                                 |
| Demo data    | `python manage.py load_demo_seed`                                          |
| API server   | `python manage.py runserver`                                               |
| Celery       | `celery -A config worker --loglevel=info`                                  |
| Test webhook | `python manage.py simulate_webhook --org-slug acme --project-slug web-api` |
| Tests        | `pytest`                                                                   |


---

## Next steps

- API and webhook details: [README.md](README.md#webhook-ingestion-api)
- Docker-based setup (macOS/Linux or Windows with Docker Desktop): [README.md](README.md#quick-start-local-development)

