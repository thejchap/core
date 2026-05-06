"""Tests for the Abode switch device."""

from unittest.mock import patch

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode.const import DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import requests_mock_fixture
from .common import setup_platform

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

AUTOMATION_ID = "switch.test_automation"
AUTOMATION_UID = "47fae27488f74f55b964a81a066c3a01"
DEVICE_ID = "switch.test_switch"
DEVICE_UID = "0012a4d3614cb7e2b8c9abea31d2fb2a"


@fixture
def _abode_setup(
    _requests: requests_mock.Mocker = Depends(requests_mock_fixture),
) -> None:
    """Wire the autouse Abode HTTP mocks for tryke."""


@test
async def entity_registry(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(hass, SWITCH_DOMAIN)

    entry = entity_registry.async_get(AUTOMATION_ID)
    expect(entry.unique_id).to_equal(AUTOMATION_UID)

    entry = entity_registry.async_get(DEVICE_ID)
    expect(entry.unique_id).to_equal(DEVICE_UID)


@test
async def attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the switch attributes are correct."""
    await setup_platform(hass, SWITCH_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    expect(state.state).to_equal(STATE_OFF)


@test
async def switch_on(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the switch can be turned on."""
    await setup_platform(hass, SWITCH_DOMAIN)

    with patch("jaraco.abode.devices.switch.Switch.switch_on") as mock_switch_on:
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await hass.async_block_till_done()
        mock_switch_on.assert_called_once()


@test
async def switch_off(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the switch can be turned off."""
    await setup_platform(hass, SWITCH_DOMAIN)

    with patch("jaraco.abode.devices.switch.Switch.switch_off") as mock_switch_off:
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await hass.async_block_till_done()
        mock_switch_off.assert_called_once()


@test
async def automation_attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the automation attributes are correct."""
    await setup_platform(hass, SWITCH_DOMAIN)

    state = hass.states.get(AUTOMATION_ID)
    # State is set based on "enabled" key in automation JSON.
    expect(state.state).to_equal(STATE_ON)


@test
async def turn_automation_off(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the automation can be turned off."""
    with patch("jaraco.abode.automation.Automation.enable") as mock_trigger:
        await setup_platform(hass, SWITCH_DOMAIN)

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: AUTOMATION_ID},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_trigger.assert_called_once_with(False)


@test
async def turn_automation_on(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the automation can be turned on."""
    with patch("jaraco.abode.automation.Automation.enable") as mock_trigger:
        await setup_platform(hass, SWITCH_DOMAIN)

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: AUTOMATION_ID},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_trigger.assert_called_once_with(True)


@test
async def trigger_automation(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the trigger automation service."""
    await setup_platform(hass, SWITCH_DOMAIN)

    with patch("jaraco.abode.automation.Automation.trigger") as mock:
        await hass.services.async_call(
            DOMAIN,
            "trigger_automation",
            {ATTR_ENTITY_ID: AUTOMATION_ID},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock.assert_called_once()
