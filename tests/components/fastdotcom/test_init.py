"""Test for fastdotcom integration init."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.fastdotcom.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import MOCK_DATA

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
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
    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("entity_id slug requires translation injection")
async def delayed_speedtest_during_startup() -> None:
    """Stub for test_delayed_speedtest_during_startup."""
