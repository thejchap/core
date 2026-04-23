"""The tests for notify_events."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.notify_events.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup of the integration."""
    config = {"notify_events": {"token": "ABC"}}
    result = await async_setup_component(hass, DOMAIN, config)
    expect(result).to_be(True)
    await hass.async_block_till_done()

    expect(DOMAIN in hass.data).to_be(True)
