from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from common import settings as settings_module
from control_plane.app import create_app


@pytest.fixture()
def client(tmp_path: pytest.TempPathFactory) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "control_plane.db"
    oss_root = tmp_path / "oss"
    old_db = settings_module.settings.db_path
    old_oss = settings_module.settings.oss_root
    settings_module.settings.db_path = str(db_path)
    settings_module.settings.oss_root = str(oss_root)
    app = create_app()
    with TestClient(app) as c:
        yield c
    settings_module.settings.db_path = old_db
    settings_module.settings.oss_root = old_oss
