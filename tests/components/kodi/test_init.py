"""Test the Kodi integration init."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.kodi.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test successful unload of entry."""
    with patch(
        "homeassistant.components.kodi.media_player.async_setup_entry",
        return_value=True,
    ):
        entry = await init_integration(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)
