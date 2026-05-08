"""The tests for the Time & Date component."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from . import load_int

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test
async def setup_and_remove_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up and removing a config entry."""
    entry = await load_int(hass)

    state = hass.states.get("sensor.time")
    expect(state is not None).to_be(True)

    expect(bool(await hass.config_entries.async_remove(entry.entry_id))).to_be(True)
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.time")).to_be(None)
