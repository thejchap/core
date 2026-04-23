"""Test for Fast.com component Init."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.fastdotcom.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import MOCK_DATA

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def unload_entry(hass: HomeAssistant = Depends(hass)) -> None:
    """Test unload an entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="UNIQUE_TEST_ID",
        title=DEFAULT_NAME,
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.fastdotcom.coordinator.fast_com",
        return_value=MOCK_DATA,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    result = await hass.config_entries.async_unload(config_entry.entry_id)
    expect(result).to_be(True)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


# delayed_speedtest_during_startup deferred: depends on
# translation-driven entity_id generation which Tryke's minimal hass
# fixture does not load.
