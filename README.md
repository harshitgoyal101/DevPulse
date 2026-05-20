# DevPulse

DevPulse is a **self-hosted CI/CD observability and alerting platform** (see Product Requirements Document `devpulse_prd.pdf`). It aims to ingest build events via webhooks and CI polling, process them asynchronously, stream live updates over WebSockets, and deliver alerts across Email, Slack, and in-app channels—with analytics such as flaky test detection and MTTR.

This repository currently implements **Phase 1 — Foundation / Milestone 1** (in progress): a Django REST API on **PostgreSQL**, **JWT authentication** with refresh rotation, **multi-tenant RBAC** (organizations, projects, memberships), **org-scoped REST APIs**, and **ingestion data models** (`WebhookDelivery`, `BuildEvent`) for webhook dedup and parsed builds. The webhook HTTP endpoint, Celery workers, Channels, Redis, and the React dashboard are **not** wired up yet; they are planned in later milestones.

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
| Webhook HTTP endpoint (HMAC, enqueue) / Celery / Redis / Channels                          | No                           |


---

## Tech stack (backend)


| Component      | Choice                                                      |
| -------------- | ----------------------------------------------------------- |
| Runtime        | Python 3.12+                                                |
| Framework      | Django 5, Django REST Framework                             |
| Authentication | JWT (SimpleJWT), token blacklist for rotated refresh tokens |
| Database       | PostgreSQL 16                                               |
| Driver         | psycopg 3                                                   |
| CORS           | `django-cors-headers` (default allows Vite dev origin)      |
| Dev tools      | pytest, pytest-django, factory-boy, ruff                    |


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
    │   ├── organizations/  # Org, Project, Membership, serializers, views, RBAC
    │   └── ingestion/      # WebhookDelivery, BuildEvent (webhook dedup + build rows)
    ├── data/
    │   └── demo_seed.json  # Demo tenants (users, orgs, projects, ingestion samples)
    └── tests/               # pytest suite (auth, permissions, org APIs, ingestion models)
```

Tests and packaging assume you run commands from `**backend/**` unless noted otherwise.

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

---

## Environment variables


| Variable               | Required (local / non-test) | Description                                                        |
| ---------------------- | --------------------------- | ------------------------------------------------------------------ |
| `DJANGO_SECRET_KEY`    | Yes                         | Django secret key; never commit real values                        |
| `DJANGO_DEBUG`         | Optional                    | Typical: `True` locally                                            |
| `DATABASE_URL`         | Yes (unless test settings)  | PostgreSQL URL, e.g. `postgres://USER:PASSWORD@HOST:5432/devpulse` |
| `ALLOWED_HOSTS`        | Optional                    | Comma-separated hosts; defaults to `localhost,127.0.0.1`           |
| `CORS_ALLOWED_ORIGINS` | Optional                    | Comma-separated origins (e.g. `http://localhost:5173` for Vite)    |


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

## Roadmap (from PRD, not implemented here)

Planned items for later milestones include:

- Webhook HTTP endpoint (HMAC verification, enqueue) and Celery worker to populate `BuildEvent` from `WebhookDelivery` (models and dedup constraint are in place)
- Full `docker-compose` (API, Celery worker, Beat, Channels, Redis)
- Real-time dashboards (Channels + Redis + React)
- Notifications, analytics, Prometheus, OpenAPI docs, seed scripts

---

## License / status

Requirements and roadmap are captured in `**devpulse_prd.pdf**`. Backend code follows the scaffold described in Milestone 1 of the Phase 1 plan; production hardening beyond this milestone is intentional future work.