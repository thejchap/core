"""Tryke fixtures for mobile_app tests (ported from conftest.py)."""

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def setup_ws(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Configure the websocket_api component."""
    assert await async_setup_component(hass, "repairs", {})
    assert await async_setup_component(hass, "websocket_api", {})
    await hass.async_block_till_done()
