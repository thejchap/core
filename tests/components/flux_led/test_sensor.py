"""Tests for flux_led sensor platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import flux_led
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import (
    FLUX_DISCOVERY,
    _mock_config_entry_for_bulb,
    _mocked_bulb,
    _patch_discovery,
    _patch_wifibulb,
)
from ._fixtures import translations

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _t: None = Depends(translations),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def paired_remotes_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the paired remotes sensor has the correct value."""
    _mock_config_entry_for_bulb(hass)
    bulb = _mocked_bulb()
    bulb.discovery = FLUX_DISCOVERY
    with _patch_discovery(device=FLUX_DISCOVERY), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "sensor.bulb_rgbcw_ddeeff_paired_remotes"
    expect(hass.states.get(entity_id).state).to_equal("2")
