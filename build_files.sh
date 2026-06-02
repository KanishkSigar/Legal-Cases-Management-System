#!/bin/bash
# Vercel build step: install deps, collect static, and (best-effort) set up the DB.
# Migrations are non-fatal: if the database can't be reached, we still deploy the
# app and surface the error in the build log instead of failing the whole build.
set -e

python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear

if [ -n "$DATABASE_URL" ]; then
  echo "=== DATABASE_URL detected — running migrations ==="
  if python3 manage.py migrate --noinput; then
    echo "=== Migrations applied successfully ==="
    python3 manage.py createadmin || echo "createadmin skipped (set ADMIN_PASSWORD)."
  else
    echo "!!! Migration failed — deploying app anyway. Check DB connectivity / env vars."
  fi
else
  echo "No DATABASE_URL at build time — skipping migrations."
fi
