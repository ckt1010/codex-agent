from __future__ import annotations

import pytest

from common.errors import ValidationError
from control_plane.repo.sqlite import SQLiteRepo
from control_plane.services.bootstrap import BootstrapService


def test_bootstrap_code_can_only_be_consumed_once(tmp_path) -> None:
    repo = SQLiteRepo(str(tmp_path / "db.sqlite"))
    svc = BootstrapService(repo, ttl_seconds=3600, token_ttl_seconds=3600)

    code, _ = svc.issue_code()
    token, expires_at = svc.consume_code(code, "mbp-work")

    assert token
    assert expires_at

    with pytest.raises(ValidationError, match="already used"):
        svc.consume_code(code, "mbp-home")


def test_bootstrap_code_expired_is_rejected(tmp_path) -> None:
    repo = SQLiteRepo(str(tmp_path / "db.sqlite"))
    svc = BootstrapService(repo, ttl_seconds=-1, token_ttl_seconds=3600)

    code, _ = svc.issue_code()

    with pytest.raises(ValidationError, match="expired"):
        svc.consume_code(code, "mbp-work")
