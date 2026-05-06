"""Tests for the Abode alarm control panel device."""

from unittest.mock import PropertyMock, patch

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode import ATTR_DEVICE_ID
from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    AlarmControlPanelState,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_DISARM,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import requests_mock_fixture
from .common import setup_platform

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

DEVICE_ID = "alarm_control_panel.abode_alarm"


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
    await setup_platform(hass, ALARM_DOMAIN)

    entry = entity_registry.async_get(DEVICE_ID)
    # Abode alarm device unique_id is the MAC address
    expect(entry.unique_id).to_equal("001122334455")


@test
async def attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the alarm control panel attributes are correct."""
    await setup_platform(hass, ALARM_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    expect(state.state).to_equal(AlarmControlPanelState.DISARMED)
    expect(state.attributes.get(ATTR_DEVICE_ID)).to_equal("area_1")
    expect(state.attributes.get("battery_backup")).to_be_falsy()
    expect(state.attributes.get("cellular_backup")).to_be_falsy()
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Abode Alarm")
    expect(state.attributes.get(ATTR_SUPPORTED_FEATURES)).to_equal(3)


@test
async def set_alarm_away(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the alarm control panel can be set to away."""
    with patch(
        "jaraco.abode.event_controller.EventController.add_device_callback"
    ) as mock_callback:
        with patch("jaraco.abode.devices.alarm.Alarm.set_away") as mock_set_away:
            await setup_platform(hass, ALARM_DOMAIN)

            await hass.services.async_call(
                ALARM_DOMAIN,
                SERVICE_ALARM_ARM_AWAY,
                {ATTR_ENTITY_ID: DEVICE_ID},
                blocking=True,
            )
            await hass.async_block_till_done()
            mock_set_away.assert_called_once()

        with patch(
            "jaraco.abode.devices.alarm.Alarm.mode",
            new_callable=PropertyMock,
        ) as mock_mode:
            mock_mode.return_value = "away"

            update_callback = mock_callback.call_args[0][1]
            await hass.async_add_executor_job(update_callback, "area_1")
            await hass.async_block_till_done()

            state = hass.states.get(DEVICE_ID)
            expect(state.state).to_equal(AlarmControlPanelState.ARMED_AWAY)


@test
async def set_alarm_home(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the alarm control panel can be set to home."""
    with patch(
        "jaraco.abode.event_controller.EventController.add_device_callback"
    ) as mock_callback:
        with patch("jaraco.abode.devices.alarm.Alarm.set_home") as mock_set_home:
            await setup_platform(hass, ALARM_DOMAIN)

            await hass.services.async_call(
                ALARM_DOMAIN,
                SERVICE_ALARM_ARM_HOME,
                {ATTR_ENTITY_ID: DEVICE_ID},
                blocking=True,
            )
            await hass.async_block_till_done()
            mock_set_home.assert_called_once()

        with patch(
            "jaraco.abode.devices.alarm.Alarm.mode", new_callable=PropertyMock
        ) as mock_mode:
            mock_mode.return_value = "home"

            update_callback = mock_callback.call_args[0][1]
            await hass.async_add_executor_job(update_callback, "area_1")
            await hass.async_block_till_done()

            state = hass.states.get(DEVICE_ID)
            expect(state.state).to_equal(AlarmControlPanelState.ARMED_HOME)


@test
async def set_alarm_standby(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the alarm control panel can be set to standby."""
    with patch(
        "jaraco.abode.event_controller.EventController.add_device_callback"
    ) as mock_callback:
        with patch("jaraco.abode.devices.alarm.Alarm.set_standby") as mock_set_standby:
            await setup_platform(hass, ALARM_DOMAIN)
            await hass.services.async_call(
                ALARM_DOMAIN,
                SERVICE_ALARM_DISARM,
                {ATTR_ENTITY_ID: DEVICE_ID},
                blocking=True,
            )
            await hass.async_block_till_done()
            mock_set_standby.assert_called_once()

        with patch(
            "jaraco.abode.devices.alarm.Alarm.mode", new_callable=PropertyMock
        ) as mock_mode:
            mock_mode.return_value = "standby"

            update_callback = mock_callback.call_args[0][1]
            await hass.async_add_executor_job(update_callback, "area_1")
            await hass.async_block_till_done()

            state = hass.states.get(DEVICE_ID)
            expect(state.state).to_equal(AlarmControlPanelState.DISARMED)


@test
async def state_unknown(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test an unknown alarm control panel state."""
    with patch(
        "jaraco.abode.devices.alarm.Alarm.mode", new_callable=PropertyMock
    ) as mock_mode:
        await setup_platform(hass, ALARM_DOMAIN)
        await hass.async_block_till_done()

        mock_mode.return_value = None

        state = hass.states.get(DEVICE_ID)
        expect(state.state).to_equal("unknown")
