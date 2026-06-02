# Deploying to Vercel (+ managed MySQL)

This app is a normal Django project, so it runs anywhere. These notes cover the
**Vercel** path specifically. Vercel runs Python **serverlessly with an ephemeral
filesystem**, so you must use an **external managed MySQL** — the app reads a single
`DATABASE_URL`.

## What's already wired up
- `vercel.json` — a single `@vercel/python` build that routes all traffic to the
  Django WSGI app (`config/wsgi.py`).
- `settings.py` — reads `DATABASE_URL` (with TLS for managed MySQL), trusts the Vercel
  host, serves static files via **WhiteNoise at runtime** (no build step needed), and
  turns on secure cookies/HSTS when `DEBUG=False`.
- `/setup/` — a one-time URL that runs `migrate` and creates the first admin from the
  browser, because the serverless host has no shell. TLS for managed MySQL is enabled
  automatically, so **`DATABASE_URL` is the only variable you must set.**

## Step 1 — Provision a MySQL database
Use any managed MySQL provider with a free tier (**Aiven**, **TiDB Cloud**, **Railway**,
**filess.io**, …). Create a database and copy its connection string:

```
mysql://USER:PASSWORD@HOST:PORT/DBNAME
```

## Step 2 — Import the repo into Vercel
- In Vercel: **Add New → Project → Import** `CaseHarbor`.
- Framework preset: **Other** (the `vercel.json` handles everything).

## Step 3 — Environment variables (Project → Settings → Environment Variables)
**Required — just one:**
| Key | Value |
|-----|-------|
| `DATABASE_URL` | your `mysql://USER:PASS@HOST:PORT/DBNAME` connection string |

That's enough to go live. TLS is auto-enabled for non-local hosts, `DEBUG` defaults to
off, static files are served by WhiteNoise, and `*.vercel.app` is already trusted.

**Optional hardening (recommended):**
| Key | Value |
|-----|-------|
| `SECRET_KEY` | a long random string (else an insecure dev key is used) |
| `SETUP_TOKEN` | a random string — if set, `/setup/` requires `?token=<it>` |

## Step 4 — Deploy
Push to `main` (auto-deploys if the GitHub repo is connected), or run:

```bash
npm i -g vercel
vercel --prod
```

## Step 5 — Initialise the database (one click, once)
After the deploy is green, visit (choose your own admin password):

```
https://<your-project>.vercel.app/setup/?username=admin&password=YourStrongPass
```

This runs the migrations and creates your admin account, then prints the result. Omit
`&password=…` to have a strong one generated and shown once. Once an admin exists the
endpoint refuses to create more, so it's safe to leave in place (or set `SETUP_TOKEN`
to lock it).

> Prefer the CLI? You can instead run `migrate` + `createadmin` locally with the same
> `DATABASE_URL` — the `/setup/` URL just exists because the serverless host has no shell.

## Step 6 — Verify
- `https://<your-project>.vercel.app/` → landing page.
- `/staff/login/` → sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` → add lawyers,
  clients, cases, appointments.

## Notes & gotchas
- **No SQLite in production** — it resets on every cold start. Always set `DATABASE_URL`.
- **Static files** are served by WhiteNoise from within the function (finders enabled),
  so styling works without a separate build step.
- **Cold starts**: the first request after idle is slower (serverless). Normal on free
  tiers.
- Pick a DB region **near your Vercel functions** (e.g. US East / `iad1`) to cut latency.
- Disable the `/setup/` endpoint after first use by clearing `SETUP_TOKEN`.
