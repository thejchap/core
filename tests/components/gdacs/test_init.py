"""Define tests for the GDACS general setup."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from ._fixtures import config_entry as config_entry_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Tryke discovery anchor."""


@test
async def component_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test that loading and unloading of a config entry works."""
    config_entry.add_to_hass(hass)
    with patch("aio_georss_gdacs.GdacsFeedManager.update") as mock_feed_manager_update:
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(mock_feed_manager_update.call_count).to_equal(1)

        expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
