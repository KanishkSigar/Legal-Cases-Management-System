#!/bin/bash
# Vercel build step: install deps, collect static files, and (when a database
# is configured) create the schema + bootstrap the admin — so a deploy is fully
# self-contained and the live site works with zero manual CLI steps.
set -e

python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear

# Only touch the database if DATABASE_URL is set (it is, in production).
if [ -n "$DATABASE_URL" ]; then
  echo "DATABASE_URL detected — running migrations…"
  python3 manage.py migrate --noinput
  # Create/refresh the admin from ADMIN_USERNAME / ADMIN_PASSWORD env vars.
  # Skips quietly if ADMIN_PASSWORD isn't set.
  python3 manage.py createadmin || true
else
  echo "No DATABASE_URL at build time — skipping migrate."
fi
