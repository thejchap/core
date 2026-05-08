"""Test DoorBird init."""

from typing import Any
from unittest.mock import MagicMock

from doorbirdpy import DoorBird, DoorBirdScheduleEntry
from tryke import Depends, expect, fixture, test

from homeassistant.components.doorbird.const import (
    CONF_EVENTS,
    DEFAULT_DOORBELL_EVENT,
    DEFAULT_MOTION_EVENT,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import (
    VALID_CONFIG,
    get_mock_doorbird_api,
    mock_not_found_exception,
    mock_unauthorized_exception,
)
from ._fixtures import (
    doorbird_info as doorbird_info_fixture,
    doorbird_schedule as doorbird_schedule_fixture,
    patch_doorbird_api_entry_points,
)

from tests.common import MockConfigEntry, load_json_value_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@fixture
def doorbird_favorites() -> dict[str, dict[str, Any]]:
    """Return a loaded DoorBird favorites fixture."""
    return load_json_value_fixture("favorites.json", "doorbird")


async def _setup_doorbird(
    hass: HomeAssistant,
    info: dict[str, Any],
    schedule: list[DoorBirdScheduleEntry],
    favorites: dict[str, dict[str, Any]],
    *,
    info_side_effect: Exception | None = None,
    favorites_side_effect: Exception | None = None,
    schedule_side_effect: Exception | None = None,
) -> tuple[MockConfigEntry, MagicMock]:
    """Create a config entry, mock the api, and run setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1CCAE3AAAAAA",
        data=VALID_CONFIG,
        options={CONF_EVENTS: [DEFAULT_DOORBELL_EVENT, DEFAULT_MOTION_EVENT]},
    )
    api = get_mock_doorbird_api(
        info=info,
        info_side_effect=info_side_effect,
        schedule=schedule,
        schedule_side_effect=schedule_side_effect,
        favorites=favorites,
        favorites_side_effect=favorites_side_effect,
    )
    entry.add_to_hass(hass)
    with patch_doorbird_api_entry_points(api):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, api


@test
async def basic_setup(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    doorbird_info: dict[str, Any] = Depends(doorbird_info_fixture),
    doorbird_schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule_fixture),
    doorbird_favorites: dict[str, dict[str, Any]] = Depends(doorbird_favorites),
) -> None:
    """Test basic setup."""
    entry, _api = await _setup_doorbird(
        hass, doorbird_info, doorbird_schedule, doorbird_favorites
    )
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def auth_fails(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    doorbird_info: dict[str, Any] = Depends(doorbird_info_fixture),
    doorbird_schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule_fixture),
    doorbird_favorites: dict[str, dict[str, Any]] = Depends(doorbird_favorites),
) -> None:
    """Test basic setup with an auth failure."""
    entry, _api = await _setup_doorbird(
        hass,
        doorbird_info,
        doorbird_schedule,
        doorbird_favorites,
        info_side_effect=mock_unauthorized_exception(),
    )
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    flows = hass.config_entries.flow.async_progress(DOMAIN)
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")


@test.cases(
    test.case("os_error", side_effect=OSError()),
    test.case("not_found", side_effect=mock_not_found_exception()),
)
async def http_info_request_fails(
    *,
    side_effect: Exception,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    doorbird_info: dict[str, Any] = Depends(doorbird_info_fixture),
    doorbird_schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule_fixture),
    doorbird_favorites: dict[str, dict[str, Any]] = Depends(doorbird_favorites),
) -> None:
    """Test basic setup with an http failure."""
    entry, _api = await _setup_doorbird(
        hass,
        doorbird_info,
        doorbird_schedule,
        doorbird_favorites,
        info_side_effect=side_effect,
    )
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def http_favorites_request_fails(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    doorbird_info: dict[str, Any] = Depends(doorbird_info_fixture),
    doorbird_schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule_fixture),
    doorbird_favorites: dict[str, dict[str, Any]] = Depends(doorbird_favorites),
) -> None:
    """Test basic setup with an http failure on favorites."""
    entry, _api = await _setup_doorbird(
        hass,
        doorbird_info,
        doorbird_schedule,
        doorbird_favorites,
        favorites_side_effect=mock_not_found_exception(),
    )
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def http_schedule_api_missing(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    doorbird_info: dict[str, Any] = Depends(doorbird_info_fixture),
    doorbird_schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule_fixture),
    doorbird_favorites: dict[str, dict[str, Any]] = Depends(doorbird_favorites),
) -> None:
    """Test missing the schedule API is non-fatal as not all models support it."""
    entry, _api = await _setup_doorbird(
        hass,
        doorbird_info,
        doorbird_schedule,
        doorbird_favorites,
        schedule_side_effect=mock_not_found_exception(),
    )
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def events_changed(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    doorbird_info: dict[str, Any] = Depends(doorbird_info_fixture),
    doorbird_schedule: list[DoorBirdScheduleEntry] = Depends(doorbird_schedule_fixture),
    doorbird_favorites: dict[str, dict[str, Any]] = Depends(doorbird_favorites),
) -> None:
    """Test changing options updates favorites and schedule."""
    entry, api = await _setup_doorbird(
        hass, doorbird_info, doorbird_schedule, doorbird_favorites
    )
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    api.favorites.reset_mock()
    api.change_favorite.reset_mock()
    api.schedule.reset_mock()

    hass.config_entries.async_update_entry(entry, options={"events": ["xyz"]})
    await hass.async_block_till_done()
    expect(len(api.favorites.mock_calls)).to_equal(2)
    expect(len(api.schedule.mock_calls)).to_equal(1)

    expect(len(api.change_favorite.mock_calls)).to_equal(1)
    favorite_type, title, url = api.change_favorite.mock_calls[0][1]
    expect(favorite_type).to_equal("http")
    expect(title).to_equal("Home Assistant (mydoorbird_xyz)")
    expect(url).to_equal(
        f"http://10.10.10.10:8123/api/doorbird/mydoorbird_xyz?token={entry.entry_id}"
    )
