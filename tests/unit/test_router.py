from __future__ import annotations

import pytest

from common.errors import ValidationError
from control_plane.services.router import route_task


def test_route_task_success() -> None:
    assert route_task("mbp-work", agent_online=True) == "mbp-work"


def test_route_task_rejects_offline_agent() -> None:
    with pytest.raises(ValidationError, match="offline"):
        route_task("mbp-work", agent_online=False)


def test_route_task_rejects_missing_target_agent() -> None:
    with pytest.raises(ValidationError, match="target_agent is required"):
        route_task("", agent_online=True)
