"""Test Brottsplatskartan component setup process."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.brottsplatskartan.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test load and unload entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "latitude": hass.config.latitude,
            "longitude": hass.config.longitude,
            "area": None,
            "app_id": "ha-1234567890",
        },
        title="BPK-HOME",
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.brottsplatskartan.sensor.BrottsplatsKartan",
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.bpk_home")
    expect(state is not None).to_be(True)

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.bpk_home")
    expect(state).to_be(None)
