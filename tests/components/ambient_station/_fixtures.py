"""Tryke fixtures for Ambient PWS."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.ambient_station.const import CONF_APP_KEY, DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.util.json import JsonArrayType, JsonObjectType

from tests.common import (
    MockConfigEntry,
    load_json_array_fixture,
    load_json_object_fixture,
)
from tests.hass_fixtures import hass


@fixture
def data_devices() -> JsonArrayType:
    """Define devices data."""
    return load_json_array_fixture("devices.json", "ambient_station")


@fixture
def data_station() -> JsonObjectType:
    """Define station data."""
    return load_json_object_fixture("station_data.json", "ambient_station")


@fixture
def api(data_devices: JsonArrayType = Depends(data_devices)) -> Mock:
    """Define a mock API object."""
    return Mock(get_devices=AsyncMock(return_value=data_devices))


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_API_KEY: "12345abcde12345abcde",
        CONF_APP_KEY: "67890fghij67890fghij",
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass),
    config: dict[str, Any] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=config,
        entry_id="382cf7643f016fd48b3fe52163fe8877",
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_aioambient(api: Mock = Depends(api)) -> Generator[None]:
    """Patch aioambient."""
    with (
        patch(
            "homeassistant.components.ambient_station.config_flow.API",
            return_value=api,
        ),
        patch("aioambient.websocket.Websocket.connect"),
    ):
        yield


@fixture
async def setup_config_entry(
    hass: HomeAssistant = Depends(hass),
    config_entry: MockConfigEntry = Depends(config_entry),
    _mock_aioambient: None = Depends(mock_aioambient),
) -> None:
    """Set up ambient_station."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
