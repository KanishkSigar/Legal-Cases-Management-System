# Legal Cases Management System

A web-based application that helps law firms and legal professionals manage
**cases, appointments, clients, and lawyers** with role-based access. It
streamlines the firm's workflow: scheduling appointments, tracking case statuses,
and managing client and lawyer information.

Built with **Django 5/6 + Bootstrap 5**, backed by **MySQL** (with a zero-config
SQLite fallback for local development).

## Features

- **Authentication & roles** — three roles, each with a tailored experience:
  - **Admin** — full access; manages lawyers, clients, cases, appointments, and the
    Django admin site.
  - **Lawyer** — sees and manages only their assigned cases and appointments; can add
    case notes and update case status.
  - **Client** — read-only view of their own cases and appointments.
- **Cases** — case number, type, status workflow (Open → In Progress → Pending →
  Closed/Won/Lost), assigned lawyer, linked client, description, and a notes timeline.
- **Clients & Lawyers** — full profile management (contact info, specialization,
  bar number, company, address).
- **Appointments** — schedule meetings between lawyers and clients, optionally tied to
  a case, with quick "mark completed / cancelled" actions.
- **Role-aware dashboard** — at-a-glance counts and recent activity.

## Tech stack

| Layer    | Choice                                   |
|----------|------------------------------------------|
| Backend  | Django (5.2+ / 6.x), Python 3.12+        |
| Frontend | Django templates + Bootstrap 5 (CDN)     |
| Database | MySQL (via PyMySQL) — SQLite fallback    |
| Forms    | django-crispy-forms + crispy-bootstrap5  |
| Config   | django-environ (`.env`)                  |

## Getting started

### 1. Clone & create a virtual environment

```bash
git clone https://github.com/KanishkSigar/Legal-Cases-Management-System.git
cd Legal-Cases-Management-System
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Edit `.env`. For a quick start with **no database setup**, use SQLite:

```ini
DB_ENGINE=sqlite
```

For **MySQL**, create the database first, then set the credentials:

```sql
CREATE DATABASE legal_cms CHARACTER SET utf8mb4;
```

```ini
DB_ENGINE=mysql
DB_NAME=legal_cms
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 3. Migrate, seed, and run

```bash
python manage.py migrate
python manage.py seed          # optional: demo users + sample data
python manage.py runserver
```

Open http://127.0.0.1:8000/.

### Demo accounts (created by `seed`)

| Role   | Username   | Password      |
|--------|------------|---------------|
| Admin  | `admin`    | `password123` |
| Lawyer | `jcarter`  | `password123` |
| Client | `rjohnson` | `password123` |

> The seeded `admin` is also a Django superuser, so `/admin/` is available.
> To create your own admin instead, run `python manage.py createsuperuser`.

## Project structure

```
config/         # project settings & root URLs
accounts/       # custom User + roles, lawyer/client profiles, dashboard, auth
cases/          # Case + CaseNote models, role-filtered views
appointments/   # Appointment model and views
templates/      # Bootstrap 5 templates
static/         # static assets
```

## Notes

- `AUTH_USER_MODEL` is a custom user (`accounts.User`) with a `role` field — this is
  set before the first migration by design.
- Access control is enforced both by view mixins (`accounts/mixins.py`) and by
  queryset scoping (`for_user`) on the `Case` and `Appointment` managers, so users
  only ever see their own records.
- Out of scope for this MVP (future ideas): document uploads, billing/invoicing,
  email notifications, and a calendar view.
