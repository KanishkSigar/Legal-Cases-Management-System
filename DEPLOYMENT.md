# Deploying to Vercel (+ managed MySQL)

This app is a normal Django project, so it runs anywhere. These notes cover the
**Vercel** path specifically. Vercel runs Python **serverlessly with an ephemeral
filesystem**, so you must use an **external managed MySQL** — the app reads a single
`DATABASE_URL`.

## What's already wired up
- `vercel.json` — two builds: the Python WSGI app (`config/wsgi.py`) and a static build
  (`build_files.sh`) whose output is served at `/static/*`.
- `api/index.py` + `config/wsgi.py` — expose the WSGI callable as `app`.
- `build_files.sh` — installs deps and runs `collectstatic` at build time.
- `settings.py` — reads `DATABASE_URL`, trusts the Vercel host, serves static via
  WhiteNoise, and turns on secure cookies when `DEBUG=False`.

## Step 1 — Provision a MySQL database
Use any managed MySQL provider (free tiers exist on **TiDB Cloud**, **Railway**,
**Aiven**, **filess.io**, etc.). Create a database and copy its connection string:

```
mysql://USER:PASSWORD@HOST:3306/DBNAME
```

## Step 2 — Import the repo into Vercel
- Push this repo to GitHub (already done).
- In Vercel: **Add New → Project → Import** `Legal-Cases-Management-System`.
- Framework preset: **Other** (the `vercel.json` handles the build).

## Step 3 — Environment variables (Project → Settings → Environment Variables)
| Key | Example / value |
|-----|-----------------|
| `DATABASE_URL` | `mysql://user:pass@host:3306/legal_cms` |
| `SECRET_KEY` | a long random string |
| `DEBUG` | `False` |
| `DB_SSL_REQUIRE` | `True` (most managed MySQL requires TLS) |
| `CSRF_TRUSTED_ORIGINS` | `https://your-project.vercel.app` |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | a strong password |

## Step 4 — Deploy
From the project root:

```bash
npm i -g vercel
vercel            # link the project (first time)
vercel --prod     # production deploy
```

…or just push to `main` if you connected the GitHub repo (auto-deploys).

## Step 5 — Create the schema (run once)
Vercel build containers don't run migrations. Apply them from your machine, pointed at
the **same** `DATABASE_URL`:

```bash
# PowerShell
$env:DATABASE_URL="mysql://user:pass@host:3306/legal_cms"; $env:DB_SSL_REQUIRE="True"
python manage.py migrate
python manage.py createadmin           # uses ADMIN_USERNAME / ADMIN_PASSWORD env, or pass flags
```

```bash
# bash
DATABASE_URL="mysql://user:pass@host:3306/legal_cms" DB_SSL_REQUIRE=True python manage.py migrate
DATABASE_URL="mysql://user:pass@host:3306/legal_cms" DB_SSL_REQUIRE=True python manage.py createadmin --username admin --password "StrongPass@123"
```

## Step 6 — Verify
- Visit `https://<your-project>.vercel.app/` → landing page.
- `/staff/login/` → sign in as the admin you created → add lawyers, clients, cases.
- If static/admin CSS is missing, re-check that the build ran `collectstatic`
  (Vercel build logs) and that `/static/app.css` resolves.

## Notes & gotchas
- **No SQLite in production** — it would reset on every cold start. Always set
  `DATABASE_URL`.
- **Migrations** are intentionally run manually (Step 5) so a deploy never blocks on a
  long migration.
- **Cold starts**: the first request after idle is slower (serverless). Normal for free
  tiers.
- Prefer a provider in a **region near your Vercel functions** to reduce DB latency.
