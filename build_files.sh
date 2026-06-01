#!/bin/bash
# Vercel build step: install deps and collect static files into ./staticfiles,
# which vercel.json serves at /static/*.
set -e
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
