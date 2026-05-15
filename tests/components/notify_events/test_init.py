"""The tests for notify_events."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.notify_events.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test setup of the integration."""
    config = {"notify_events": {"token": "ABC"}}
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_block_till_done()

    expect(DOMAIN in hass.data).to_be(True)
