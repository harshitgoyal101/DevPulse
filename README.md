# DevPulse

DevPulse is a **self-hosted CI/CD observability and alerting platform** (see Product Requirements Document `devpulse_prd.pdf`). It aims to ingest build events via webhooks and CI polling, process them asynchronously, stream live updates over WebSockets, and deliver alerts across Email, Slack, and in-app channels—with analytics such as flaky test detection and MTTR.

This repository implements **Phase 1 — Foundation**: a Django REST API on **PostgreSQL** and **Redis**, **JWT authentication** with refresh rotation, **multi-tenant RBAC**, **org-scoped REST APIs**, **webhook ingestion** (HMAC verification, deduplication, async Celery processing into `BuildEvent`), and a **React (Vite) frontend** with login and an org/project dashboard shell. **Phase 2** (Channels, live WebSocket timeline, CI polling) is not started yet.

---

## Implemented today


| Area                                                                                       | Status                       |
| ------------------------------------------------------------------------------------------ | ---------------------------- |
| Django 5 + Django REST Framework                                                           | Yes                          |
| PostgreSQL 16 (via Docker Compose)                                                         | Yes                          |
| JWT (`djangorestframework-simplejwt`): 15m access, 7d refresh, rotation + blacklist        | Yes                          |
| Custom user model (email login, UUID primary keys)                                         | Yes                          |
| RBAC models: Organization, Project, OrganizationMembership (`admin` / `member` / `viewer`) | Yes                          |
| Django Admin for User, Org, Project, Membership                                            | Yes                          |
| Ingestion models: `WebhookDelivery`, `BuildEvent` (dedup + parsed builds, admin, tests)    | Yes                          |
| Auth API: login, refresh, `/me`                                                            | Yes                          |
| Org/project/membership REST APIs (`/api/orgs/…`) with RBAC                                 | Yes                          |
| Permission helpers (`IsOrganizationMember`, `HasOrganizationRole`, org-scoped mixins)      | Yes (enforced on org routes) |
| React frontend (Vite): login, logout, org/project dashboard shell                            | Yes                          |
| Per-project `webhook_secret` (admins see on project detail API)                            | Yes                          |
| Webhook HTTP endpoint: HMAC/token verify, dedup, 202 + Celery enqueue                      | Yes                          |
| Celery worker + Redis broker (local or Docker Compose)                                       | Yes                          |
| Docker Compose: Postgres, Redis, API, Celery worker                                        | Yes                          |
| Django Channels / live WebSocket dashboards                                                | No (Phase 2)                 |


---

## Tech stack (backend)


| Component      | Choice                                                      |
| -------------- | ----------------------------------------------------------- |
| Runtime        | Python 3.12+                                                |
| Framework      | Django 5, Django REST Framework                             |
| Authentication | JWT (SimpleJWT), token blacklist for rotated refresh tokens |
| Task queue     | Celery 5 + Redis 7                                          |
| Database       | PostgreSQL 16                                               |
| Driver         | psycopg 3                                                   |
| CORS           | `django-cors-headers` (default allows Vite dev origin)      |
| Dev tools      | pytest, pytest-django, factory-boy, ruff                    |


---

## Repository layout

```
DevPulse/
├── devpulse_prd.pdf          # Product requirements
├── docker-compose.yml        # Postgres, Redis, API, Celery worker
├── .env.example              # Sample environment variables
├── README.md                 # This file
└── backend/
    ├── manage.py
    ├── pyproject.toml       # Dependencies and tool config
    ├── config/              # Project settings (base / local / test), URLs, WSGI, ASGI
    ├── apps/
    │   ├── accounts/       # Custom User, Me API, JWT consumer
    │   ├── organizations/  # Org, Project, Membership, serializers, views, RBAC
    │   └── ingestion/      # WebhookDelivery, BuildEvent (webhook dedup + build rows)
    ├── data/
    │   └── demo_seed.json  # Demo tenants (users, orgs, projects, ingestion samples)
    └── tests/               # pytest suite (auth, permissions, org APIs, ingestion models)
└── frontend/                # React 18 + Vite (login, logout, protected home)
```

Tests and packaging assume you run commands from `**backend/**` unless noted otherwise.

---

## Prerequisites

- **Python 3.12+**
- **Docker** and **Docker Compose** (for PostgreSQL locally)
- A virtual environment (`python -m venv .venv`) is recommended

---

## Quick start (local development)

### 1. Start infrastructure (Postgres + Redis)

From the repository root:

```bash
docker compose up -d postgres redis
```

Or start the **full Phase 1 stack** (Postgres, Redis, Django API, Celery worker):

```bash
docker compose up -d
docker compose exec api python manage.py migrate
docker compose exec api python manage.py load_demo_seed
```

Postgres listens on **5432**; Redis on **6379**; API on **8000**.

### 2. Configure environment variables

Copy the example file and edit secrets:

```bash
cp .env.example .env
```

Variables are loaded from `**.env` in the repo root** (next to `docker-compose.yml`), not inside `backend/`.

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

You should see migrations for Django apps, `**accounts**` (custom user), `**organizations**`, `**ingestion**`, and `**token_blacklist**` (required for refresh rotation).

### 5. Load demo data (optional)

A JSON seed file defines sample users, orgs, projects, memberships, webhook deliveries, and build events:

```bash
python manage.py load_demo_seed
```

Source: [`backend/data/demo_seed.json`](backend/data/demo_seed.json). All demo users share password `demo-password123` (see `default_password` in the file). The seed includes **4 organizations** with **10 projects** each, **20 users**, cross-org memberships, **16 webhook deliveries**, and **40 build events**. Example login: `alice@acme.dev` (admin on Acme Corp, viewer on Beta Labs).

Re-run safely; existing rows are updated by stable UUID. Use `--reset-passwords` after changing `default_password` in the JSON.

### 6. Create an admin user (optional)

```bash
python manage.py createsuperuser
```

Enter **email** and password when prompted (there is no `username` field).

### 7. Run the API

```bash
python manage.py runserver
```

- API base: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**
- Admin: **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)**

### 8. Run the frontend (optional)

From the repo root (Node 18+):

```bash
cd frontend
npm install
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)**. Vite proxies `/api` to Django (`frontend/vite.config.ts`). CORS allows `http://localhost:5173` in local settings.

Sign in with a demo user (after `load_demo_seed`), e.g. `alice@acme.dev` / `demo-password123`. Log out blacklists the refresh token via `POST /api/auth/token/blacklist/`.

---

## Environment variables


| Variable               | Required (local / non-test) | Description                                                        |
| ---------------------- | --------------------------- | ------------------------------------------------------------------ |
| `DJANGO_SECRET_KEY`    | Yes                         | Django secret key; never commit real values                        |
| `DJANGO_DEBUG`         | Optional                    | Typical: `True` locally                                            |
| `DATABASE_URL`         | Yes (unless test settings)  | PostgreSQL URL, e.g. `postgres://USER:PASSWORD@HOST:5432/devpulse` |
| `ALLOWED_HOSTS`        | Optional                    | Comma-separated hosts; defaults to `localhost,127.0.0.1`           |
| `CORS_ALLOWED_ORIGINS` | Optional                    | Comma-separated origins (e.g. `http://localhost:5173` for Vite)    |
| `REDIS_URL`            | Optional                    | Default `redis://localhost:6379/0`                                 |
| `CELERY_BROKER_URL`    | Optional                    | Defaults to `REDIS_URL`                                          |
| `WEBHOOK_BASE_URL`     | Optional                    | Base URL for webhook docs/simulator (default `http://127.0.0.1:8000`) |


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

- `**access`** — short-lived JWT (15 minutes, configured in `SIMPLE_JWT`)
- `**refresh**` — refresh token (7 days), invalidated after rotation when used with blacklist enabled

The request body uses `**email**` (not `username`) because the custom user model sets `USERNAME_FIELD = "email"`.

### Refresh (with rotation)

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{"refresh": "<refresh-token>"}
```

Returns a **new** access token and **new** refresh token when `ROTATE_REFRESH_TOKENS` is enabled.

### Log out (blacklist refresh)

```http
POST /api/auth/token/blacklist/
Content-Type: application/json

{"refresh": "<refresh-token>"}
```

Returns **205**. The refresh token cannot be used again. The React app calls this on logout.

### Current user

```http
GET /api/auth/me/
Authorization: Bearer <access-token>
```

**Response (200)** includes `id`, `email`, `first_name`, `last_name`, `date_joined` (no password fields).

Unauthenticated requests return **401**.

There is **no public registration endpoint** yet; create users via `createsuperuser` or the admin.

---

## Webhook ingestion API

Public endpoint (no JWT). Project is identified in the URL; signature uses the project’s `webhook_secret` (visible to org **admins** on `GET /api/orgs/{org_id}/projects/{project_id}/`).

```http
POST /api/webhooks/{provider}/{project_id}/
```

`provider` is `github` or `gitlab`.

| Provider | Verification header | Delivery ID header |
| -------- | ------------------- | ------------------ |
| GitHub   | `X-Hub-Signature-256` (`sha256=` HMAC-SHA256 of raw body) | `X-GitHub-Delivery` |
| GitLab   | `X-Gitlab-Token` (constant-time compare to secret) | `X-Gitlab-Event-UUID` |

**Responses**

- **202** — accepted (new delivery enqueued, or duplicate delivery ID already recorded)
- **401** — invalid signature/token
- **404** — unknown provider or project

Supported payload shapes (MVP): GitHub `workflow_run` (completed/in progress), GitLab `pipeline` `object_attributes`. The Celery worker writes a `BuildEvent` linked to the `WebhookDelivery`.

**Simulate locally** (after `load_demo_seed`):

```bash
cd backend
python manage.py simulate_webhook --org-slug acme-corp --project-slug web-api
```

Uses fixture [`backend/apps/ingestion/fixtures/github_workflow_run.json`](backend/apps/ingestion/fixtures/github_workflow_run.json). Demo projects use predictable secrets: `demo-{org_slug}-{project_slug}-webhook-secret`.

---

## Organizations API

All org routes require a valid JWT (`Authorization: Bearer <access-token>`). Organization IDs and project IDs are UUIDs.

### Organizations


| Method   | Path                  | Minimum role                                      |
| -------- | --------------------- | ------------------------------------------------- |
| `GET`    | `/api/orgs/`          | Authenticated (lists orgs you belong to)          |
| `POST`   | `/api/orgs/`          | Authenticated (creates org; you become **admin**) |
| `GET`    | `/api/orgs/{org_id}/` | `viewer`                                          |
| `PATCH`  | `/api/orgs/{org_id}/` | `admin`                                           |
| `DELETE` | `/api/orgs/{org_id}/` | `admin`                                           |


**Create organization**

```http
POST /api/orgs/
Content-Type: application/json
Authorization: Bearer <access-token>

{"name": "Acme Corp", "slug": "acme-corp"}
```

**Response (201)** includes `id`, `name`, `slug`, `created_at`, `updated_at`. A membership row is created automatically with role `admin` for the caller.

**Organization detail (GET)** also includes a nested `projects` array.

### Projects (org-scoped)


| Method   | Path                                        | Minimum role |
| -------- | ------------------------------------------- | ------------ |
| `GET`    | `/api/orgs/{org_id}/projects/`              | `viewer`     |
| `POST`   | `/api/orgs/{org_id}/projects/`              | `admin`      |
| `GET`    | `/api/orgs/{org_id}/projects/{project_id}/` | `viewer`     |
| `PATCH`  | `/api/orgs/{org_id}/projects/{project_id}/` | `admin`      |
| `DELETE` | `/api/orgs/{org_id}/projects/{project_id}/` | `admin`      |


**Create project**

```http
POST /api/orgs/{org_id}/projects/
Content-Type: application/json
Authorization: Bearer <access-token>

{"name": "Web API", "slug": "web-api"}
```

`slug` must be unique within the organization. Responses include `organization_id` (read-only).

### Memberships (org-scoped)


| Method   | Path                                              | Minimum role |
| -------- | ------------------------------------------------- | ------------ |
| `GET`    | `/api/orgs/{org_id}/memberships/`                 | `viewer`     |
| `POST`   | `/api/orgs/{org_id}/memberships/`                 | `admin`      |
| `GET`    | `/api/orgs/{org_id}/memberships/{membership_id}/` | `viewer`     |
| `PATCH`  | `/api/orgs/{org_id}/memberships/{membership_id}/` | `admin`      |
| `DELETE` | `/api/orgs/{org_id}/memberships/{membership_id}/` | `admin`      |


**Add member**

```http
POST /api/orgs/{org_id}/memberships/
Content-Type: application/json
Authorization: Bearer <access-token>

{"user_id": "<uuid-of-existing-user>", "role": "member"}
```

List/detail responses include `user_id`, `email`, `role`, and `created_at`. Only **existing** users can be added (no self-registration flow).

### RBAC and errors

Role rank: `admin` > `member` > `viewer`. Views use `HasOrganizationRole` with a per-method minimum role (`OrgRBACMixin` in `backend/apps/organizations/mixins.py`).

- **401** — missing or invalid JWT
- **403** — authenticated but insufficient role, or not a member of the org in the URL
- **404** — org/project/membership not found, or resource belongs to a different org than `{org_id}` in the path

---

## Data model (RBAC)

High-level relationships:

- `**Organization`** — tenant; `**slug**` is globally unique for simple URLs.
- `**Project**` — belongs to one organization; `**slug**` is unique **per organization** (two orgs may both use `slug=web`).
- `**OrganizationMembership`** — links `**User**` ↔ `**Organization**` with `**role**`:
  - `admin` — manage members, projects, and org settings (enforced on mutating org routes)
  - `member` — between viewer and admin (used for future build/notification features)
  - `viewer` — read-only access to org resources

Users can belong to **multiple** organizations via separate membership rows.

### Ingestion models

Defined in `backend/apps/ingestion/models.py` (FK to `**Project**` only; no public list API yet):

- `**WebhookDelivery**` — one row per provider delivery ID for deduplication before async processing. Unique on `(provider, delivery_id)` where `provider` is `github` or `gitlab`. `received_at` is set on insert.
- `**BuildEvent**` — normalized build/run parsed from a webhook payload: `status`, `branch`, `commit_sha`, optional `duration` (seconds), `raw_payload` (JSON), `created_at`. Indexes on `(project, created_at)` and `(status, branch)`.

`BuildStatus` values: `pending`, `success`, `failure`, `cancelled`, `skipped`.

**Permission helpers** in `backend/apps/organizations/permissions.py`:

- `get_user_organizations(user)`
- `get_user_role(user, org_id)`
- `IsOrganizationMember`
- `HasOrganizationRole` (reads `required_org_role` on the view, defaults to `viewer`)

**Mixins** in `backend/apps/organizations/mixins.py`:

- `UserOrganizationsQuerysetMixin` — list/detail scoped to the user's orgs
- `OrgScopedQuerysetMixin` — nested resources filtered by `{org_id}` in the URL
- `OrgRBACMixin` — sets read vs write minimum role from the HTTP method

---

## Django Admin

Use the admin to manage:

- Users (email-based)
- Organizations, projects, and memberships
- Webhook deliveries and build events (debugging ingestion; seed via admin or tests until the webhook API exists)

Use the admin or the [Organizations API](#organizations-api) to seed orgs, projects, and memberships.

---

## Tests and linting

From `**backend/`** with the virtual environment activated:

```bash
pytest
```

```bash
ruff check apps config manage.py tests
```

`pytest` uses `**config.settings.test**` (see `backend/pyproject.toml` `[tool.pytest.ini_options]`).

---

## Roadmap (Phase 2+, from PRD)

- Django Channels + Redis pub/sub + live build timeline (WebSocket)
- CI API polling via Celery Beat
- Build list REST API for dashboard
- Notifications (Email, Slack, in-app), analytics, Prometheus, OpenAPI docs

---

## License / status

Requirements and roadmap are captured in `**devpulse_prd.pdf**`. Phase 1 (webhooks, Celery, Redis, docker-compose) is implemented; Phase 2+ is intentional future work.