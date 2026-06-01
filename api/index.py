"""Vercel serverless entrypoint — exposes the Django WSGI app."""
from config.wsgi import application as app  # noqa: F401
