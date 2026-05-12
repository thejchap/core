"""The switch tests for the Airzone Cloud platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant

from ._fixtures import airzone_cloud_no_websockets
from .util import async_init_integration

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _no_ws: None = Depends(airzone_cloud_no_websockets),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def airzone_create_switches(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creation of switches."""
    await async_init_integration(hass)

    state = hass.states.get("switch.dormitorio")
    expect(state.state).to_equal(STATE_OFF)

    state = hass.states.get("switch.salon")
    expect(state.state).to_equal(STATE_ON)


@test
async def airzone_switch_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test switch off."""
    await async_init_integration(hass)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.salon"},
            blocking=True,
        )

    state = hass.states.get("switch.salon")
    expect(state.state).to_equal(STATE_OFF)


@test
async def airzone_switch_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test switch on."""
    await async_init_integration(hass)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.dormitorio"},
            blocking=True,
        )

    state = hass.states.get("switch.dormitorio")
    expect(state.state).to_equal(STATE_ON)
