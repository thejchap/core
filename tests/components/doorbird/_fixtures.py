"""Tryke fixtures for DoorBird tests."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

from doorbirdpy import DoorBird, DoorBirdScheduleEntry
from tryke import Depends, fixture

from . import get_mock_doorbird_api

from tests.common import load_json_value_fixture


@contextmanager
def patch_doorbird_api_entry_points(api: MagicMock) -> Generator[DoorBird]:
    """Mock the DoorBirdAPI."""
    with (
        patch(
            "homeassistant.components.doorbird.DoorBird",
            return_value=api,
        ),
        patch(
            "homeassistant.components.doorbird.config_flow.DoorBird",
            return_value=api,
        ),
        patch(
            "homeassistant.components.doorbird.device.get_url",
            return_value="http://127.0.0.1:8123",
        ),
    ):
        yield api


@fixture
def doorbird_info() -> dict[str, Any]:
    """Return a loaded DoorBird info fixture."""
    return load_json_value_fixture("info.json", "doorbird")["BHA"]["VERSION"][0]


@fixture
def doorbird_schedule() -> list[DoorBirdScheduleEntry]:
    """Return a loaded DoorBird schedule fixture."""
    return DoorBirdScheduleEntry.parse_all(
        load_json_value_fixture("schedule.json", "doorbird")
    )


@fixture
def doorbird_api(
    info: dict[str, Any] = Depends(doorbird_info),
    schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule),
) -> Generator[DoorBird]:
    """Mock the DoorBirdAPI."""
    api = get_mock_doorbird_api(info=info, schedule=schedule)
    with patch_doorbird_api_entry_points(api):
        yield api
