from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_data_root(monkeypatch):
    tmp = Path(tempfile.mkdtemp(prefix="ice-test-"))
    for sub in ("agents", "skills", "files", "users", "tasks", ".cache"):
        (tmp / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DATA_ROOT", str(tmp))
    monkeypatch.setenv("ICE_SECRET_KEY", "test-secret-key-with-enough-length-32b")

    # purge cached settings/paths
    from app.core import config as cfg
    from app.core.storage import index_db, paths as p

    cfg.get_settings.cache_clear()
    p.get_paths.cache_clear()
    index_db.get_index_db.cache_clear()

    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)
