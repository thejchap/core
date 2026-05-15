"""Test config init."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def config_setup(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test it sets up hassbian."""
    await async_setup_component(hass, "config", {})
    expect("config" in hass.config.components).to_be(True)
