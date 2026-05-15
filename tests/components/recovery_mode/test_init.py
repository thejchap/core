"""Tests for the Recovery Mode integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import async_get_persistent_notifications
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def works(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test Recovery Mode works."""
    expect(await async_setup_component(hass, "recovery_mode", {})).to_be_truthy()
    await hass.async_block_till_done()
    notifications = async_get_persistent_notifications(hass)
    expect(len(notifications)).to_equal(1)
