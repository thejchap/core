"""Test the init file code."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test
from zeversolar import ZeverSolarData
from zeversolar.exceptions import ZeverSolarTimeout

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    config_entry as config_entry_fixture,
    zeversolar_data as zeversolar_data_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def async_setup_entry_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    zeversolar_data: ZeverSolarData = Depends(zeversolar_data_fixture),
) -> None:
    """Test to load/unload the integration."""

    config_entry.add_to_hass(hass)

    with patch("zeversolar.ZeverSolarClient.get_data", side_effect=ZeverSolarTimeout):
        await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    with (
        patch("homeassistant.components.zeversolar.PLATFORMS", []),
        patch("zeversolar.ZeverSolarClient.get_data", return_value=zeversolar_data),
    ):
        hass.config_entries.async_schedule_reload(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    with patch("homeassistant.components.zeversolar.PLATFORMS", []):
        result = await hass.config_entries.async_unload(config_entry.entry_id)
    expect(result).to_be(True)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
