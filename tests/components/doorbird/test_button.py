"""Test DoorBird buttons."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import DoorbirdMockerType, doorbird_mocker

from tests.hass_fixtures import hass as hass_fixture, mock_network


_FAKE_TRANSLATIONS = {
    "component.doorbird.entity.button.ir.name": "IR",
    "component.doorbird.entity.button.reset_favorites.name": "Reset favorites",
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _translations() -> None:
    """Inject translations so IR and reset_favorites button slugs include their suffix."""
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _t: None = Depends(_translations),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def relay_button(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mocker: DoorbirdMockerType = Depends(doorbird_mocker),
) -> None:
    """Test pressing a relay button."""
    doorbird_entry = await mocker()
    relay_1_entity_id = "button.mydoorbird_relay_1"
    expect(hass.states.get(relay_1_entity_id).state).to_be(STATE_UNKNOWN)
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: relay_1_entity_id}, blocking=True
    )
    expect(hass.states.get(relay_1_entity_id).state != STATE_UNKNOWN).to_be(True)
    expect(doorbird_entry.api.energize_relay.call_count).to_equal(1)


@test
async def ir_button(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mocker: DoorbirdMockerType = Depends(doorbird_mocker),
) -> None:
    """Test pressing the IR button."""
    doorbird_entry = await mocker()
    ir_entity_id = "button.mydoorbird_ir"
    expect(hass.states.get(ir_entity_id).state).to_be(STATE_UNKNOWN)
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: ir_entity_id}, blocking=True
    )
    expect(hass.states.get(ir_entity_id).state != STATE_UNKNOWN).to_be(True)
    expect(doorbird_entry.api.turn_light_on.call_count).to_equal(1)


@test
async def reset_favorites_button(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mocker: DoorbirdMockerType = Depends(doorbird_mocker),
) -> None:
    """Test pressing the reset favorites button."""
    doorbird_entry = await mocker()
    reset_entity_id = "button.mydoorbird_reset_favorites"
    expect(hass.states.get(reset_entity_id).state).to_be(STATE_UNKNOWN)
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: reset_entity_id}, blocking=True
    )
    expect(hass.states.get(reset_entity_id).state != STATE_UNKNOWN).to_be(True)
    expect(doorbird_entry.api.delete_favorite.call_count).to_equal(3)
