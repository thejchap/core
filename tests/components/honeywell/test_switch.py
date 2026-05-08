"""Tests for Honeywell switch component."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiosomecomfort.exceptions import SomeComfortError
from tryke import Depends, fixture, test

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import init_integration
from ._fixtures import client, config_entry as config_entry_fx, device as device_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


_FAKE_TRANSLATIONS = {
    "component.honeywell.entity.switch.emergency_heat.name": "Emergency heat",
    "component.honeywell.exceptions.switch_failed_on.message":
        "Failed to switch on",
    "component.honeywell.exceptions.switch_failed_off.message":
        "Failed to switch off",
}


async def _fake_get_translations(hass, language, category, integrations=None, config_flow=None):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _client: MagicMock = Depends(client),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def emheat_switch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    device: AsyncMock = Depends(device_fx),
) -> None:
    """Test emergency heat switch."""
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
        await init_integration(hass, config_entry)
    entity_id = f"switch.{device.name}_emergency_heat"
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    device.set_system_mode.assert_called_once_with("emheat")

    device.set_system_mode.reset_mock()

    device.system_mode = "emheat"
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    device.set_system_mode.assert_called_once_with("off")

    device.set_system_mode.reset_mock()
    device.system_mode = "heat"
    device.set_system_mode.side_effect = SomeComfortError
    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    device.set_system_mode.assert_called_once_with("emheat")

    device.set_system_mode.reset_mock()
    device.system_mode = "emheat"
    device.set_system_mode.side_effect = SomeComfortError
    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    device.set_system_mode.assert_called_once_with("off")
