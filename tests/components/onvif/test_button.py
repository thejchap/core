"""Test button of ONVIF integration."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, ButtonDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import MAC, setup_onvif_integration

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
def _trigger_executor() -> None:
    """Module-local resolution anchor — see PATTERNS.md."""


@test
async def reboot_button(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test states of the Reboot button."""
    await setup_onvif_integration(hass)

    state = hass.states.get("button.testcamera_reboot")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(ButtonDeviceClass.RESTART)

    entry = entity_registry.async_get("button.testcamera_reboot")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{MAC}_reboot")


@test
async def reboot_button_press(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Reboot button press."""
    _, camera, _ = await setup_onvif_integration(hass)
    devicemgmt = await camera.create_devicemgmt_service()
    devicemgmt.SystemReboot = AsyncMock(return_value=True)

    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {ATTR_ENTITY_ID: "button.testcamera_reboot"},
        blocking=True,
    )
    await hass.async_block_till_done()

    devicemgmt.SystemReboot.assert_called_once()


@test
async def set_dateandtime_button(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test states of the SetDateAndTime button."""
    await setup_onvif_integration(hass)

    state = hass.states.get("button.testcamera_set_system_date_and_time")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)

    entry = entity_registry.async_get("button.testcamera_set_system_date_and_time")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{MAC}_setsystemdatetime")


@test
async def set_dateandtime_button_press(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test SetDateAndTime button press."""
    _, _camera, device = await setup_onvif_integration(hass)
    device.async_manually_set_date_and_time = AsyncMock(return_value=True)

    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {ATTR_ENTITY_ID: "button.testcamera_set_system_date_and_time"},
        blocking=True,
    )
    await hass.async_block_till_done()

    device.async_manually_set_date_and_time.assert_called_once()
