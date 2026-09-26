"""
WSGI entrypoint used by gunicorn (see orderservice.service).

Runs schema initialization once at process startup, then exposes the Flask
app object for gunicorn to serve.
"""
import logging
import time

from app import app, ensure_schema

logger = logging.getLogger("orderservice.wsgi")

for attempt in range(5):
    try:
        ensure_schema()
        logger.info("Database schema ready.")
        break
    except Exception as exc:  # noqa: BLE001
        logger.warning("Schema init failed (attempt %s/5): %s", attempt + 1, exc)
        time.sleep(3)
