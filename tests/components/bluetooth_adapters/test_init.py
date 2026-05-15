"""Test the Bluetooth Adapters setup."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth_adapters import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture


@fixture
def _trigger_executor(
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Ensure we can setup."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
