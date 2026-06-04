# ⚖️ CaseHarbor — Legal Cases Management System

[![CI](https://github.com/KanishkSigar/CaseHarbor/actions/workflows/ci.yml/badge.svg)](https://github.com/KanishkSigar/CaseHarbor/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-caseharbor.onrender.com-2ea44f?style=flat&logo=render)](https://caseharbor.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5%2F6-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-relational-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A role-based web application that helps law firms run their day-to-day operations —
**cases, appointments, lawyers and clients** — on top of a clean, normalised
**relational database**. Three user roles (Admin, Lawyer, Client) each get a tailored,
access-controlled view, with permissions enforced **at the database-query level**, not
just hidden in the UI.

### 🔗 Live app → **[caseharbor.onrender.com](https://caseharbor.onrender.com)**  ·  📄 Overview → **[kanishksigar.me/CaseHarbor](https://kanishksigar.me/CaseHarbor/)**
The landing page is public. Sign in at **/staff/login/** (admin) or **/login/**
(client/lawyer). *Note: the free host sleeps when idle, so the first load can take
~30–60 s to wake.*

> **The focus of this project is the data layer** — how a handful of well-designed
> tables, foreign keys and query-scoping rules model an entire legal practice. The
> [Database Schema](#-database-schema--the-heart-of-the-system) section below is the
> highlight.

**Stack:** Django 5/6 · PostgreSQL / MySQL · Bootstrap 5 · WhiteNoise · deployed on Render.

---

## Table of contents
- [Features](#-features)
- [Tech stack](#-tech-stack)
- [Database schema — the heart of the system](#-database-schema--the-heart-of-the-system)
- [How the database handles everything](#-how-the-database-handles-everything)
- [Authentication & roles](#-authentication--roles)
- [Getting started (local)](#-getting-started-local)
- [Deployment (Vercel + managed MySQL)](#-deployment-vercel--managed-mysql)
- [Project structure](#-project-structure)

---

## ✨ Features

| Area | What it does |
|------|--------------|
| **Public landing page** | Marketing-style entry point with a live data-model showcase — no login required. |
| **Separate logins** | A **client/lawyer portal** and an **unadvertised admin portal** with different credential windows. Admins cannot log in through the public portal and vice-versa. |
| **Cases** | Case number, type, full status workflow (Open → In Progress → Pending → Closed/Won/Lost), assigned lawyer, linked client, description, and a **notes timeline**. |
| **Appointments** | Schedule meetings between a lawyer and a client, optionally tied to a case, with one-click *complete / cancel*. |
| **Lawyers & clients** | Full CRUD on profiles (specialisation, bar number, company, contact). Each is backed by a real login account. |
| **Our Lawyers directory** | A read-only directory every signed-in user can browse. |
| **Role-aware dashboard** | Counts and recent activity scoped to who you are. |
| **No seed clutter** | Ships empty. One `createadmin` command bootstraps the first administrator; all real data is entered through the app. |

---

## 🧰 Tech stack

| Layer | Choice |
|-------|--------|
| Backend | **Django** (5.2+ / 6.x), Python 3.12+ |
| Database | **MySQL** via `PyMySQL` (pure-Python driver — no C compiler needed) |
| Frontend | Django templates + **Bootstrap 5** + custom CSS (navy/gold theme) |
| Forms | `django-crispy-forms` + `crispy-bootstrap5` |
| Static files | `WhiteNoise` (compressed, hashed, served in-process) |
| Config | `django-environ` + `dj-database-url` (12-factor, single `DATABASE_URL`) |
| Hosting | **Render** (one-blueprint deploy, app + Postgres) — or Vercel + MySQL |

---

## 🗄️ Database schema — the heart of the system

The entire practice is modelled by **five core tables** plus Django's auth/session
infrastructure. Everything links back to a single `User` table through foreign keys.

```mermaid
erDiagram
    USER ||--o| LAWYERPROFILE : "1-to-1"
    USER ||--o| CLIENTPROFILE : "1-to-1"
    LAWYERPROFILE ||--o{ CASE : "handles"
    CLIENTPROFILE ||--o{ CASE : "owns"
    CASE ||--o{ CASENOTE : "has timeline"
    LAWYERPROFILE ||--o{ APPOINTMENT : "attends"
    CLIENTPROFILE ||--o{ APPOINTMENT : "attends"
    CASE ||--o{ APPOINTMENT : "optionally about"
    USER ||--o{ CASENOTE : "authored"

    USER {
        bigint id PK
        varchar username UK
        varchar password "hashed (PBKDF2)"
        varchar role "ADMIN | LAWYER | CLIENT"
        varchar first_name
        varchar last_name
        varchar email
        varchar phone
        bool is_staff
        bool is_superuser
    }
    LAWYERPROFILE {
        bigint id PK
        bigint user_id FK "UNIQUE -> USER"
        varchar specialization
        varchar bar_number
        text bio
    }
    CLIENTPROFILE {
        bigint id PK
        bigint user_id FK "UNIQUE -> USER"
        varchar address
        varchar company
    }
    CASE {
        bigint id PK
        varchar case_number UK
        varchar title
        text description
        varchar case_type "CIVIL | CRIMINAL | FAMILY | ..."
        varchar status "OPEN | WON | LOST | ..."
        bigint client_id FK "-> CLIENTPROFILE (PROTECT)"
        bigint lawyer_id FK "-> LAWYERPROFILE (PROTECT)"
        date opened_date
        date closed_date "nullable"
        datetime created_at
        datetime updated_at
    }
    CASENOTE {
        bigint id PK
        bigint case_id FK "-> CASE (CASCADE)"
        bigint author_id FK "-> USER (SET NULL)"
        text text
        datetime created_at
    }
    APPOINTMENT {
        bigint id PK
        varchar title
        datetime scheduled_for
        varchar location
        bigint lawyer_id FK "-> LAWYERPROFILE (CASCADE)"
        bigint client_id FK "-> CLIENTPROFILE (CASCADE)"
        bigint case_id FK "-> CASE (SET NULL, nullable)"
        varchar status "SCHEDULED | COMPLETED | CANCELLED"
        text notes
        datetime created_at
    }
```

### Table-by-table

#### 1. `accounts_user` — one identity table for everyone
A **custom user model** (`AbstractUser` + a `role` column). Instead of three separate
login tables, every person — admin, lawyer or client — is one row here. The `role`
field is the single source of truth that drives every permission decision.
`username` is unique; passwords are stored hashed (PBKDF2).

#### 2. `accounts_lawyerprofile` / `accounts_clientprofile` — domain data, kept separate
Each is a **one-to-one** extension of `User` (`user_id` is `UNIQUE`). This keeps
role-specific fields (a lawyer's `bar_number`, a client's `company`) out of the auth
table — a clean separation of *who you are* from *what you are in the firm*. Deleting a
profile cascades from the user; deleting the app-side profile also removes the account.

#### 3. `cases_case` — the central entity
Joins a **client** and a **lawyer** together. Both foreign keys use
**`on_delete=PROTECT`** — you cannot delete a client or lawyer who still has cases,
which prevents orphaned legal records. `case_number` is `UNIQUE`. `status` and
`case_type` are constrained to enumerated choices, and the table is ordered by
`-opened_date` for sensible default listings.

#### 4. `cases_casenote` — an append-only timeline
A one-to-many child of `Case` (`on_delete=CASCADE` — notes die with their case). The
`author` points at `User` with **`on_delete=SET NULL`**, so the audit trail survives
even if the authoring account is later removed.

#### 5. `appointments_appointment` — scheduling
References a `lawyer` and a `client` (`CASCADE`) and **optionally** a `case`
(`on_delete=SET NULL`, nullable) — an appointment can exist before a case is opened.
Ordered by `scheduled_for` so calendars read chronologically.

### Why these `on_delete` choices matter
| Relationship | Rule | Reason |
|--------------|------|--------|
| Case → Client / Lawyer | `PROTECT` | Never silently lose a legal record by deleting a person. |
| CaseNote → Case | `CASCADE` | Notes are meaningless without their case. |
| CaseNote → Author | `SET NULL` | Preserve the timeline even if the author leaves. |
| Appointment → Case | `SET NULL` | Appointments outlive / predate cases. |

---

## ⚙️ How the database handles everything

The interesting part isn't just the tables — it's how access rules live **in the data
layer**:

- **Query-level role scoping.** Both `Case` and `Appointment` expose a custom manager
  method `for_user(user)` that returns a different `QuerySet` per role:

  ```python
  # cases/models.py
  class CaseQuerySet(models.QuerySet):
      def for_user(self, user):
          if user.is_admin:   return self                       # sees all
          if user.is_lawyer:  return self.filter(lawyer__user=user)   # WHERE lawyer.user_id = ?
          if user.is_client:  return self.filter(client__user=user)   # WHERE client.user_id = ?
          return self.none()
  ```

  A client literally **cannot** load another client's case — the row never leaves the
  database for them. The generated SQL joins `cases_case → accounts_clientprofile` and
  filters on `user_id`, so the isolation is enforced by the query, not the template.

- **Referential integrity** is delegated to MySQL via foreign keys, so the app can't
  create dangling references even under concurrent writes.

- **Enumerated columns** (`status`, `case_type`, `role`) use Django `TextChoices`,
  which keeps invalid states out of the table while staying human-readable.

- **`select_related`** is used on every list/detail view so a page of cases is one SQL
  query with joins, not N+1 lookups.

- **Migrations** are the schema's version control — every table change is a reviewable,
  replayable file under each app's `migrations/`.

---

## 🔐 Authentication & roles

| Role | Logs in at | Can do |
|------|-----------|--------|
| **Admin** | `/staff/login/` (separate, unadvertised) | Everything: manage lawyers, clients, cases, appointments, plus Django admin. |
| **Lawyer** | `/login/` (client/lawyer portal) | See & manage **only their** assigned cases and appointments; add notes; update status. |
| **Client** | `/login/` | **Read-only** view of their own cases and appointments. |

The two portals reject the wrong audience: an admin who tries the public portal is told
to use the staff portal, and a non-admin who finds the staff portal is refused. Access
is also enforced server-side by `RoleRequiredMixin` / `AdminRequiredMixin`
(`accounts/mixins.py`) on top of the query scoping above.

---

## 🚀 Getting started (local)

```bash
git clone https://github.com/KanishkSigar/CaseHarbor.git
cd CaseHarbor

python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

copy .env.example .env         # macOS/Linux: cp .env.example .env
```

**Pick a database** in `.env`:

```ini
# Easiest — zero-config local file DB:
DB_ENGINE=sqlite
```
or point at a real MySQL:
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

**Run it:**

```bash
python manage.py migrate
python manage.py createadmin --username admin --password "ChangeMe@123"
python manage.py runserver 8800
```

Open **http://127.0.0.1:8800/** — the landing page. Admins sign in at
`/staff/login/`; create lawyers and clients from **Manage**, and they sign in at
`/login/`.

> If port 8000 gives *"You don't have permission to access that port"* on Windows,
> it's reserved by Hyper-V/WSL — just use another port like `8800`.

---

## ☁️ Deployment

**Recommended — Render (free, one click):** the repo ships a `render.yaml` blueprint
that provisions a **free PostgreSQL database and the web service together** and links
them automatically (no credentials to copy, `SECRET_KEY` auto-generated, migrations run
at build). Go to **render.com → New → Blueprint → pick this repo → Apply**, then create
your admin by visiting `/setup/?username=admin&password=YourPass` once.

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for both Render and the Vercel + MySQL path. The
Vercel path is summarised below.

### Vercel + managed MySQL

Vercel runs Python serverlessly with an **ephemeral filesystem**, so production needs an
**external MySQL** (SQLite can't persist there). The app reads one env var,
`DATABASE_URL`, so any managed MySQL works (Railway, Aiven, TiDB Cloud, etc.).

1. **Provision a MySQL database** and copy its connection string:
   ```
   mysql://USER:PASSWORD@HOST:3306/DBNAME
   ```
2. **Set one Vercel environment variable** (Project → Settings → Environment Variables):
   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | your `mysql://USER:PASS@HOST:PORT/DBNAME` connection string |

   TLS is auto-enabled for managed hosts, `DEBUG` defaults off, and `*.vercel.app` is
   trusted — so this is the only required var. (Optionally add `SECRET_KEY` and a
   `SETUP_TOKEN` for extra hardening.)
3. **Deploy:** push to `main` (auto-deploys if the repo is connected), or run
   `npm i -g vercel && vercel --prod`. `vercel.json` routes all traffic to the Django
   WSGI app; static files are served by WhiteNoise at runtime (no build step).
4. **Initialise the database once** by visiting
   `https://<your-project>.vercel.app/setup/?username=admin&password=YourStrongPass` — it
   runs the migrations and creates your admin from the browser (the serverless host has
   no shell). Repeat visits are refused once an admin exists.

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the full step-by-step.

---

## 📁 Project structure

```
config/         # settings (env + DATABASE_URL), root URLs, WSGI
accounts/       # custom User + roles, profiles, landing, dual logins, dashboard,
                #   lawyer/client management, createadmin command
cases/          # Case + CaseNote models, role-scoped views, notes timeline
appointments/   # Appointment model and scheduling views
templates/      # Bootstrap 5 templates (landing, auth, app pages)
static/         # theme CSS
vercel.json     # Vercel build & routing config (single Python build → config/wsgi.py)
```

---

## 🧭 Roadmap / out of scope (next iterations)
Document uploads per case · billing & invoicing · email/SMS reminders · a calendar
view for appointments · full-text search across cases.
