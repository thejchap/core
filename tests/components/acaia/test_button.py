"""Tests for the acaia buttons."""

from datetime import timedelta
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_scale

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import freezer as freezer_fixture, hass as hass_fixture

BUTTONS = (
    "tare",
    "reset_timer",
    "start_stop_timer",
)


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def buttons() -> None:
    """Test the acaia buttons (snapshot platform)."""


@test
async def button_presses(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the acaia button presses."""
    await setup_integration(hass, mock_config_entry)

    for button in BUTTONS:
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: f"button.lunar_ddeeff_{button}"},
            blocking=True,
        )
        function = getattr(mock_scale, button)
        function.assert_called_once()


@test
async def buttons_unavailable_on_disconnected_scale(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test the acaia buttons are unavailable when the scale is disconnected."""
    await setup_integration(hass, mock_config_entry)

    for button in BUTTONS:
        state = hass.states.get(f"button.lunar_ddeeff_{button}")
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(STATE_UNKNOWN)

    mock_scale.connected = False
    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for button in BUTTONS:
        state = hass.states.get(f"button.lunar_ddeeff_{button}")
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(STATE_UNAVAILABLE)
