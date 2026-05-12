"""Tryke fixtures for DoorBird tests."""

from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

from doorbirdpy import DoorBird, DoorBirdScheduleEntry
from tryke import Depends, fixture

from homeassistant.components.doorbird.const import (
    CONF_EVENTS,
    DEFAULT_DOORBELL_EVENT,
    DEFAULT_MOTION_EVENT,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from . import VALID_CONFIG, get_mock_doorbird_api

from tests.common import MockConfigEntry, load_json_value_fixture
from tests.hass_fixtures import hass as hass_fixture


@dataclass
class MockDoorbirdEntry:
    """Mock DoorBird config entry."""

    entry: MockConfigEntry
    api: MagicMock


type DoorbirdMockerType = Callable[..., Coroutine[Any, Any, MockDoorbirdEntry]]


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
def doorbird_favorites() -> dict[str, dict[str, Any]]:
    """Return a loaded DoorBird favorites fixture."""
    return load_json_value_fixture("favorites.json", "doorbird")


@fixture
def doorbird_api(
    info: dict[str, Any] = Depends(doorbird_info),
    schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule),
) -> Generator[DoorBird]:
    """Mock the DoorBirdAPI."""
    api = get_mock_doorbird_api(info=info, schedule=schedule)
    with patch_doorbird_api_entry_points(api):
        yield api


def make_doorbird_mocker(
    hass: HomeAssistant,
    doorbird_info: dict[str, Any],
    doorbird_schedule: list[DoorBirdScheduleEntry],
    doorbird_favorites: dict[str, dict[str, Any]],
) -> DoorbirdMockerType:
    """Build the doorbird_mocker callable used across tests."""

    async def _async_mock(
        entry: MockConfigEntry | None = None,
        api: DoorBird | None = None,
        change_schedule: tuple[bool, int] | None = None,
        info: dict[str, Any] | None = None,
        info_side_effect: Exception | None = None,
        schedule: list[DoorBirdScheduleEntry] | None = None,
        schedule_side_effect: Exception | None = None,
        favorites: dict[str, dict[str, Any]] | None = None,
        favorites_side_effect: Exception | None = None,
        options: dict[str, Any] | None = None,
    ) -> MockDoorbirdEntry:
        """Create a MockDoorbirdEntry from defaults or specific values."""
        entry = entry or MockConfigEntry(
            domain=DOMAIN,
            unique_id="1CCAE3AAAAAA",
            data=VALID_CONFIG,
            options=options
            or {CONF_EVENTS: [DEFAULT_DOORBELL_EVENT, DEFAULT_MOTION_EVENT]},
        )
        api = api or get_mock_doorbird_api(
            info=info or doorbird_info,
            info_side_effect=info_side_effect,
            schedule=schedule or doorbird_schedule,
            schedule_side_effect=schedule_side_effect,
            favorites=favorites or doorbird_favorites,
            favorites_side_effect=favorites_side_effect,
            change_schedule=change_schedule,
        )
        entry.add_to_hass(hass)
        with patch_doorbird_api_entry_points(api):
            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
        return MockDoorbirdEntry(entry=entry, api=api)

    return _async_mock


@fixture
async def doorbird_mocker(
    hass: HomeAssistant = Depends(hass_fixture),
    info: dict[str, Any] = Depends(doorbird_info),
    schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule),
    favorites: dict[str, dict[str, Any]] = Depends(doorbird_favorites),
) -> DoorbirdMockerType:
    """Create a MockDoorbirdEntry factory."""
    return make_doorbird_mocker(hass, info, schedule, favorites)
