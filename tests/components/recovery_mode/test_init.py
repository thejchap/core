"""Tests for the Recovery Mode integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import async_get_persistent_notifications
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def works(hass: HomeAssistant = Depends(hass)) -> None:
    """Test Recovery Mode works."""
    result = await async_setup_component(hass, "recovery_mode", {})
    expect(result).to_be(True)
    await hass.async_block_till_done()
    notifications = async_get_persistent_notifications(hass)
    expect(len(notifications)).to_equal(1)
