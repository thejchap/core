"""Test the Tesla Wall Connector config flow."""

from tesla_wall_connector.exceptions import WallConnectorConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .conftest import create_wall_connector_entry, get_lifetime_mock, get_vitals_mock

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test
async def init_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup and that we get the device info, including firmware version."""
    entry = await create_wall_connector_entry(
        hass, vitals_data=get_vitals_mock(), lifetime_data=get_lifetime_mock()
    )

    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def init_while_offline(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init with the wall connector offline."""
    entry = await create_wall_connector_entry(
        hass, side_effect=WallConnectorConnectionError
    )

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def load_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Config entry can be unloaded."""
    entry = await create_wall_connector_entry(
        hass, vitals_data=get_vitals_mock(), lifetime_data=get_lifetime_mock()
    )
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
