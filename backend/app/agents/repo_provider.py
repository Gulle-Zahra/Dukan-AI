"""Single switch between the real DB repo and the in-memory fake (USE_FAKE_REPO in .env)."""
import logging
import os

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("dukaan.repo")

USE_FAKE_REPO = os.getenv("USE_FAKE_REPO", "false").strip().lower() in ("1", "true", "yes")

if USE_FAKE_REPO:
    from app.agents import _fake_repo as repo
    log.warning("USE_FAKE_REPO=true -> using in-memory fake repo")
else:
    from app.db import repo  # noqa: F401

__all__ = ["repo", "USE_FAKE_REPO"]
