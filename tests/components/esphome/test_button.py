"""Test ESPHome buttones."""

from unittest.mock import call

from aioesphomeapi import APIClient, ButtonInfo
from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import MockESPHomeDeviceType, mock_client, mock_esphome_device

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def button_generic_entity(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic button entity."""
    entity_info = [
        ButtonInfo(
            object_id="mybutton",
            key=1,
            name="my button",
        )
    ]
    states = []
    user_service = []
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("button.test_my_button")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.test_my_button"},
        blocking=True,
    )
    mock_client.button_command.assert_has_calls([call(1, device_id=0)])
    state = hass.states.get("button.test_my_button")
    expect(state is not None).to_be(True)
    expect(state.state != STATE_UNKNOWN).to_be(True)

    await mock_device.mock_disconnect(False)
    state = hass.states.get("button.test_my_button")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNAVAILABLE)
