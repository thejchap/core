"""Test the Intelligent Storage Acceleration setup."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.isal import DOMAIN
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
    """Ensure we can setup."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
