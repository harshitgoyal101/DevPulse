# DevPulse

DevPulse is a **self-hosted CI/CD observability and alerting platform** (see Product Requirements Document `devpulse_prd.pdf`). It aims to ingest build events via webhooks and CI polling, process them asynchronously, stream live updates over WebSockets, and deliver alerts across Email, Slack, and in-app channels—with analytics such as flaky test detection and MTTR.

This repository currently implements **Phase 1 — Foundation / Milestone 1** only: a Django REST API scaffold on **PostgreSQL**, **JWT authentication** with refresh rotation, and **multi-tenant RBAC data models** (organizations and projects). Webhooks, Celery, Channels, Redis, and the React dashboard are **not** in this repo yet; they are planned in later milestones.

---

## Implemented today

| Area | Status |
|------|--------|
| Django 5 + Django REST Framework | Yes |
| PostgreSQL 16 (via Docker Compose) | Yes |
| JWT (`djangorestframework-simplejwt`): 15m access, 7d refresh, rotation + blacklist | Yes |
| Custom user model (email login, UUID primary keys) | Yes |
| RBAC models: Organization, Project, OrganizationMembership (`admin` / `member` / `viewer`) | Yes |
| Django Admin for User, Org, Project, Membership | Yes |
| Auth API: login, refresh, `/me` | Yes |
| Permission helpers (`IsOrganizationMember`, `HasOrganizationRole`, etc.) | Yes (stub for future routes) |
| Org/project REST CRUD | No |
| Celery / Redis / webhooks / Channels | No |

---

## Tech stack (backend)

| Component | Choice |
|-----------|--------|
| Runtime | Python 3.12+ |
| Framework | Django 5, Django REST Framework |
| Authentication | JWT (SimpleJWT), token blacklist for rotated refresh tokens |
| Database | PostgreSQL 16 |
| Driver | psycopg 3 |
| CORS | `django-cors-headers` (default allows Vite dev origin) |
| Dev tools | pytest, pytest-django, factory-boy, ruff |

---

## Repository layout

```
DevPulse/
├── devpulse_prd.pdf          # Product requirements
├── docker-compose.yml        # PostgreSQL 16 only (local dev)
├── .env.example              # Sample environment variables
├── README.md                 # This file
└── backend/
    ├── manage.py
    ├── pyproject.toml       # Dependencies and tool config
    ├── config/              # Project settings (base / local / test), URLs, WSGI, ASGI
    ├── apps/
    │   ├── accounts/       # Custom User, Me API, JWT consumer
    │   └── organizations/  # Org, Project, Membership, RBAC helpers
    └── tests/               # pytest suite
```

Tests and packaging assume you run commands from **`backend/`** unless noted otherwise.

---

## Prerequisites

- **Python 3.12+**
- **Docker** and **Docker Compose** (for PostgreSQL locally)
- A virtual environment (`python -m venv .venv`) is recommended

---

## Quick start (local development)

### 1. Start PostgreSQL

From the repository root:

```bash
docker compose up -d
```

This starts Postgres 16 with database `devpulse`, user `devpulse`, password `devpulse`, on port **5432**.

### 2. Configure environment variables

Copy the example file and edit secrets:

```bash
cp .env.example .env
```

Variables are loaded from **`.env` in the repo root** (next to `docker-compose.yml`), not inside `backend/`.

See [Environment variables](#environment-variables) below.

### 3. Install the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 4. Apply migrations

Local settings module defaults via `manage.py` to `config.settings.local`.

```bash
export DJANGO_SETTINGS_MODULE=config.settings.local   # optional; manage.py sets this by default
python manage.py migrate
```

You should see migrations for Django apps, **`accounts`** (custom user), **`organizations`**, and **`token_blacklist`** (required for refresh rotation).

### 5. Create an admin user (optional)

```bash
python manage.py createsuperuser
```

Enter **email** and password when prompted (there is no `username` field).

### 6. Run the API

```bash
python manage.py runserver
```

- API base: **http://127.0.0.1:8000/**
- Admin: **http://127.0.0.1:8000/admin/**

---

## Environment variables

| Variable | Required (local / non-test) | Description |
|----------|------------------------------|-------------|
| `DJANGO_SECRET_KEY` | Yes | Django secret key; never commit real values |
| `DJANGO_DEBUG` | Optional | Typical: `True` locally |
| `DATABASE_URL` | Yes (unless test settings) | PostgreSQL URL, e.g. `postgres://USER:PASSWORD@HOST:5432/devpulse` |
| `ALLOWED_HOSTS` | Optional | Comma-separated hosts; defaults to `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Optional | Comma-separated origins (e.g. `http://localhost:5173` for Vite) |

**Tests** use `config.settings.test` (SQLite in-memory, fast password hasher). When `DJANGO_SETTINGS_MODULE` ends with `.test`, `DATABASE_URL` and `DJANGO_SECRET_KEY` are not required—see `backend/config/settings/base.py` and `backend/config/settings/test.py`.

---

## Authentication API

All endpoints return JSON unless otherwise noted.

### Obtain access + refresh tokens

```http
POST /api/auth/token/
Content-Type: application/json

{"email": "you@example.com", "password": "your-password"}
```

**Response (200)** includes:

- **`access`** — short-lived JWT (15 minutes, configured in `SIMPLE_JWT`)
- **`refresh`** — refresh token (7 days), invalidated after rotation when used with blacklist enabled

The request body uses **`email`** (not `username`) because the custom user model sets `USERNAME_FIELD = "email"`.

### Refresh (with rotation)

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{"refresh": "<refresh-token>"}
```

Returns a **new** access token and **new** refresh token; the previous refresh token is blacklisted so it cannot be reused.

### Current user

```http
GET /api/auth/me/
Authorization: Bearer <access-token>
```

**Response (200)** includes `id`, `email`, `first_name`, `last_name`, `date_joined` (no password fields).

Unauthenticated requests return **401**.

There is **no public registration endpoint** yet; create users via `createsuperuser` or the admin.

---

## Data model (RBAC)

High-level relationships:

- **`Organization`** — tenant; **`slug`** is globally unique for simple URLs.
- **`Project`** — belongs to one organization; **`slug`** is unique **per organization** (two orgs may both use `slug=web`).
- **`OrganizationMembership`** — links **`User`** ↔ **`Organization`** with **`role`**:
  - `admin` — intended for managing members, projects, alert rules (enforced later in views)
  - `member` — intended for builds and personal notification preferences
  - `viewer` — read-only

Users can belong to **multiple** organizations via separate membership rows.

**Permission helpers** in `backend/apps/organizations/permissions.py` (for future scoped routes):

- `get_user_organizations(user)`
- `get_user_role(user, org_id)`
- `IsOrganizationMember`
- `HasOrganizationRole` (reads `required_org_role` on the view, defaults to `viewer`)

`backend/apps/organizations/mixins.py` documents a future pattern for org-scoped querysets.

---

## Django Admin

Use the admin to manage:

- Users (email-based)
- Organizations, projects, and memberships

This is the primary way to seed orgs and roles until org/project APIs exist.

---

## Tests and linting

From **`backend/`** with the virtual environment activated:

```bash
pytest
```

```bash
ruff check apps config manage.py tests
```

`pytest` uses **`config.settings.test`** (see `backend/pyproject.toml` `[tool.pytest.ini_options]`).

---

## Roadmap (from PRD, not implemented here)

Planned items for later milestones include:

- Webhook ingestion (HMAC, deduplication, Celery workers)
- Full `docker-compose` (API, Celery worker, Beat, Channels, Redis)
- Real-time dashboards (Channels + Redis + React)
- Notifications, analytics, Prometheus, OpenAPI docs, seed scripts

---

## License / status

Requirements and roadmap are captured in **`devpulse_prd.pdf`**. Backend code follows the scaffold described in Milestone 1 of the Phase 1 plan; production hardening beyond this milestone is intentional future work.
