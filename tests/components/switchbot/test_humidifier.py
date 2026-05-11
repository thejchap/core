"""Test the switchbot humidifiers."""

from collections.abc import Callable
from unittest.mock import AsyncMock, patch

from switchbot import SwitchbotOperationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.humidifier import (
    ATTR_HUMIDITY,
    ATTR_MODE,
    DOMAIN as HUMIDIFIER_DOMAIN,
    MODE_AUTO,
    MODE_NORMAL,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_MODE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import EVAPORATIVE_HUMIDIFIER_SERVICE_INFO, HUMIDIFIER_SERVICE_INFO
from ._fixtures import mock_entry_encrypted_factory, mock_entry_factory

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test.cases(
    test.case("turn-off", service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off", expected_args=()),
    test.case("turn-on", service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on", expected_args=()),
    test.case("set-humidity", service=SERVICE_SET_HUMIDITY, service_data={ATTR_HUMIDITY: 50}, mock_method="set_humidity_level", expected_args=(50,)),
    test.case("set-mode-auto", service=SERVICE_SET_MODE, service_data={ATTR_MODE: MODE_AUTO}, mock_method="set_auto_mode", expected_args=()),
    test.case("set-mode-normal", service=SERVICE_SET_MODE, service_data={ATTR_MODE: MODE_NORMAL}, mock_method="set_manual_mode", expected_args=()),
)
async def humidifier_services(
    service: str,
    service_data: dict,
    mock_method: str,
    expected_args: tuple,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(mock_entry_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all humidifier services with proper parameters."""
    inject_bluetooth_service_info(hass, HUMIDIFIER_SERVICE_INFO)

    entry = entry_factory(sensor_type="humidifier")
    entry.add_to_hass(hass)
    entity_id = "humidifier.test_name"

    with (
        patch(
            "homeassistant.components.switchbot.humidifier.switchbot.SwitchbotHumidifier.set_level",
            new=AsyncMock(return_value=True),
        ) as mock_set_humidity_level,
        patch(
            "homeassistant.components.switchbot.humidifier.switchbot.SwitchbotHumidifier.async_set_auto",
            new=AsyncMock(return_value=True),
        ) as mock_set_auto_mode,
        patch(
            "homeassistant.components.switchbot.humidifier.switchbot.SwitchbotHumidifier.async_set_manual",
            new=AsyncMock(return_value=True),
        ) as mock_set_manual_mode,
        patch(
            "homeassistant.components.switchbot.humidifier.switchbot.SwitchbotHumidifier.turn_off",
            new=AsyncMock(return_value=True),
        ) as mock_turn_off,
        patch(
            "homeassistant.components.switchbot.humidifier.switchbot.SwitchbotHumidifier.turn_on",
            new=AsyncMock(return_value=True),
        ) as mock_turn_on,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        await hass.services.async_call(
            HUMIDIFIER_DOMAIN,
            service,
            {**service_data, ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mock_map = {
            "turn_off": mock_turn_off,
            "turn_on": mock_turn_on,
            "set_humidity_level": mock_set_humidity_level,
            "set_auto_mode": mock_set_auto_mode,
            "set_manual_mode": mock_set_manual_mode,
        }
        mock_map[mock_method].assert_awaited_once_with(*expected_args)


@test.cases(
    test.case("turn-on", service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("turn-off", service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("set-humidity", service=SERVICE_SET_HUMIDITY, service_data={ATTR_HUMIDITY: 60}, mock_method="set_level"),
    test.case("set-mode-auto", service=SERVICE_SET_MODE, service_data={ATTR_MODE: MODE_AUTO}, mock_method="async_set_auto"),
    test.case("set-mode-normal", service=SERVICE_SET_MODE, service_data={ATTR_MODE: MODE_NORMAL}, mock_method="async_set_manual"),
)
async def exception_handling_humidifier_service(
    service: str,
    service_data: dict,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(mock_entry_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test exception handling for humidifier service with exception."""
    inject_bluetooth_service_info(hass, HUMIDIFIER_SERVICE_INFO)

    entry = entry_factory(sensor_type="humidifier")
    entry.add_to_hass(hass)
    entity_id = "humidifier.test_name"

    patch_target = f"homeassistant.components.switchbot.humidifier.switchbot.SwitchbotHumidifier.{mock_method}"

    with patch(patch_target, new=AsyncMock(side_effect=SwitchbotOperationError("Operation failed"))):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        raised = False
        try:
            await hass.services.async_call(
                HUMIDIFIER_DOMAIN,
                service,
                {**service_data, ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except HomeAssistantError:
            raised = True
        expect(raised).to_be(True)


@test.cases(
    test.case("turn-on", service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("turn-off", service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("set-humidity", service=SERVICE_SET_HUMIDITY, service_data={ATTR_HUMIDITY: 60}, mock_method="set_target_humidity"),
    test.case("set-mode-sleep", service=SERVICE_SET_MODE, service_data={ATTR_MODE: "sleep"}, mock_method="set_mode"),
)
async def evaporative_humidifier_services(
    service: str,
    service_data: dict,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(
        mock_entry_encrypted_factory
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test evaporative humidifier services with proper parameters."""
    inject_bluetooth_service_info(hass, EVAPORATIVE_HUMIDIFIER_SERVICE_INFO)

    entry = entry_factory(sensor_type="evaporative_humidifier")
    entry.add_to_hass(hass)
    entity_id = "humidifier.test_name"

    mocked_instance = AsyncMock(return_value=True)
    with patch.multiple(
        "homeassistant.components.switchbot.humidifier.switchbot.SwitchbotEvaporativeHumidifier",
        update=AsyncMock(return_value=None),
        **{mock_method: mocked_instance},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        await hass.services.async_call(
            HUMIDIFIER_DOMAIN,
            service,
            {**service_data, ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mocked_instance.assert_awaited_once()


@test.cases(
    test.case("turn-on", service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("turn-off", service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("set-humidity", service=SERVICE_SET_HUMIDITY, service_data={ATTR_HUMIDITY: 60}, mock_method="set_target_humidity"),
    test.case("set-mode-sleep", service=SERVICE_SET_MODE, service_data={ATTR_MODE: "sleep"}, mock_method="set_mode"),
)
async def evaporative_humidifier_services_with_exception(
    service: str,
    service_data: dict,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(
        mock_entry_encrypted_factory
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test exception handling for evaporative humidifier services."""
    inject_bluetooth_service_info(hass, EVAPORATIVE_HUMIDIFIER_SERVICE_INFO)

    entry = entry_factory(sensor_type="evaporative_humidifier")
    entry.add_to_hass(hass)
    entity_id = "humidifier.test_name"

    patch_target = f"homeassistant.components.switchbot.humidifier.switchbot.SwitchbotEvaporativeHumidifier.{mock_method}"

    with patch(
        patch_target,
        new=AsyncMock(side_effect=SwitchbotOperationError("Operation failed")),
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        raised = False
        try:
            await hass.services.async_call(
                HUMIDIFIER_DOMAIN,
                service,
                {**service_data, ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except HomeAssistantError:
            raised = True
        expect(raised).to_be(True)
