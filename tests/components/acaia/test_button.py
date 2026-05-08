"""Tests for the acaia buttons."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_scale

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    enable_bluetooth,
    freezer as freezer_fixture,
    hass as hass_fixture,
)

BUTTONS = (
    "tare",
    "reset_timer",
    "start_stop_timer",
)


# Inject acaia button translations so entity_id slugs include _tare, etc.
_FAKE_TRANSLATIONS = {
    "component.acaia.entity.button.reset_timer.name": "Reset timer",
    "component.acaia.entity.button.start_stop.name": "Start/stop timer",
    "component.acaia.entity.button.tare.name": "Tare",
    "component.acaia.entity.binary_sensor.timer_running.name": "Timer running",
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    if integrations and "acaia" in integrations:
        return _FAKE_TRANSLATIONS
    return {}


@fixture
def _trigger_executor(_bluetooth: None = Depends(enable_bluetooth)) -> None:
    """Force tryke to build a per-module HookExecutor and enable bluetooth."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def buttons() -> None:
    """Stub for test_buttons (snapshot-based)."""


@test
async def button_presses(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the acaia button presses."""
    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        side_effect=_fake_get_translations,
    ):
        await setup_integration(hass, mock_config_entry)

    for button in BUTTONS:
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {
                ATTR_ENTITY_ID: f"button.lunar_ddeeff_{button}",
            },
            blocking=True,
        )

        function = getattr(mock_scale, button)
        function.assert_called_once()


@test
async def buttons_unavailable_on_disconnected_scale(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_scale: MagicMock = Depends(mock_scale),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test the acaia buttons are unavailable when the scale is disconnected."""
    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        side_effect=_fake_get_translations,
    ):
        await setup_integration(hass, mock_config_entry)

    for button in BUTTONS:
        state = hass.states.get(f"button.lunar_ddeeff_{button}")
        expect(state is not None).to_be(True)
        expect(state.state).to_equal(STATE_UNKNOWN)

    mock_scale.connected = False
    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for button in BUTTONS:
        state = hass.states.get(f"button.lunar_ddeeff_{button}")
        expect(state is not None).to_be(True)
        expect(state.state).to_equal(STATE_UNAVAILABLE)
