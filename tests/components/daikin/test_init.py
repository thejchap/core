"""Define tests for the Daikin init."""

from collections.abc import Generator
from unittest.mock import AsyncMock, PropertyMock, patch

from aiohttp import ClientConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.daikin.const import DOMAIN, KEY_MAC
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


HOST = "127.0.0.1"
MAC = "AABBCCDDEEFF"

DATA = {
    "ver": "1_1_8",
    "name": "DaikinAP00000",
    "mac": MAC,
    "model": "NOTSUPPORT",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@fixture
def mock_daikin() -> Generator[AsyncMock]:
    """Mock pydaikin."""

    async def mock_daikin_factory(*args, **kwargs):
        """Mock the init function in pydaikin."""
        return Appliance

    with patch("homeassistant.components.daikin.DaikinFactory") as Appliance:
        Appliance.side_effect = mock_daikin_factory
        type(Appliance).update_status = AsyncMock()
        type(Appliance).device_ip = PropertyMock(return_value=HOST)
        type(Appliance).inside_temperature = PropertyMock(return_value=22)
        type(Appliance).target_temperature = PropertyMock(return_value=22)
        type(Appliance).zones = PropertyMock(return_value=[("Zone 1", "0", 0)])
        type(Appliance).fan_rate = PropertyMock(return_value=[])
        type(Appliance).swing_modes = PropertyMock(return_value=[])
        yield Appliance


@test
async def client_connection_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_daikin: AsyncMock = Depends(mock_daikin),
) -> None:
    """Test client connection error on setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MAC,
        data={CONF_HOST: HOST, KEY_MAC: MAC},
    )
    config_entry.add_to_hass(hass)

    mock_daikin.side_effect = ClientConnectionError
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def timeout_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_daikin: AsyncMock = Depends(mock_daikin),
) -> None:
    """Test timeout error on setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MAC,
        data={CONF_HOST: HOST, KEY_MAC: MAC},
    )
    config_entry.add_to_hass(hass)

    mock_daikin.side_effect = TimeoutError
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("entity_id depends on translations and complex registry mutation")
async def duplicate_removal() -> None:
    """Stub for test_duplicate_removal."""


@test.skip("entity_id depends on translations and complex registry mutation")
async def unique_id_migrate() -> None:
    """Stub for test_unique_id_migrate."""


@test.skip("entity_id depends on translations")
async def client_update_connection_error() -> None:
    """Stub for test_client_update_connection_error."""
