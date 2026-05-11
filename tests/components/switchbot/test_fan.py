"""Test the switchbot fan."""

from collections.abc import Callable
from unittest.mock import AsyncMock, patch

from switchbot import SwitchbotOperationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.fan import (
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_OSCILLATE,
    SERVICE_SET_PERCENTAGE,
    SERVICE_SET_PRESET_MODE,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import (
    AIR_PURIFIER_JP_SERVICE_INFO,
    AIR_PURIFIER_TABLE_JP_SERVICE_INFO,
    AIR_PURIFIER_TABLE_US_SERVICE_INFO,
    AIR_PURIFIER_US_SERVICE_INFO,
    CIRCULATOR_FAN_SERVICE_INFO,
)
from ._fixtures import mock_entry_encrypted_factory, mock_entry_factory

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test.cases(
    test.case("set-preset-baby", service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "baby"}, mock_method="set_preset_mode"),
    test.case("set-percentage", service=SERVICE_SET_PERCENTAGE, service_data={ATTR_PERCENTAGE: 27}, mock_method="set_percentage"),
    test.case("oscillate", service=SERVICE_OSCILLATE, service_data={ATTR_OSCILLATING: True}, mock_method="set_oscillation"),
    test.case("turn-off", service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("turn-on", service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
)
async def circulator_fan_controlling(
    service: str,
    service_data: dict,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(mock_entry_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test controlling the circulator fan with different services."""
    inject_bluetooth_service_info(hass, CIRCULATOR_FAN_SERVICE_INFO)

    entry = entry_factory(sensor_type="circulator_fan")
    entity_id = "fan.test_name"
    entry.add_to_hass(hass)

    mocked_instance = AsyncMock(return_value=True)
    mocked_none_instance = AsyncMock(return_value=None)
    with patch.multiple(
        "homeassistant.components.switchbot.fan.switchbot.SwitchbotFan",
        get_basic_info=mocked_none_instance,
        **{mock_method: mocked_instance},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        await hass.services.async_call(
            FAN_DOMAIN,
            service,
            {**service_data, ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mocked_instance.assert_awaited_once()


@test.cases(
    test.case("jp-set-preset-sleep", sensor_type="air_purifier_jp", service_info=AIR_PURIFIER_JP_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("jp-set-percentage", sensor_type="air_purifier_jp", service_info=AIR_PURIFIER_JP_SERVICE_INFO, service=SERVICE_SET_PERCENTAGE, service_data={ATTR_PERCENTAGE: 27}, mock_method="set_percentage"),
    test.case("jp-turn-off", sensor_type="air_purifier_jp", service_info=AIR_PURIFIER_JP_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("jp-turn-on", sensor_type="air_purifier_jp", service_info=AIR_PURIFIER_JP_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("table-jp-set-preset-sleep", sensor_type="air_purifier_table_jp", service_info=AIR_PURIFIER_TABLE_JP_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("table-jp-set-percentage", sensor_type="air_purifier_table_jp", service_info=AIR_PURIFIER_TABLE_JP_SERVICE_INFO, service=SERVICE_SET_PERCENTAGE, service_data={ATTR_PERCENTAGE: 27}, mock_method="set_percentage"),
    test.case("table-jp-turn-off", sensor_type="air_purifier_table_jp", service_info=AIR_PURIFIER_TABLE_JP_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("table-jp-turn-on", sensor_type="air_purifier_table_jp", service_info=AIR_PURIFIER_TABLE_JP_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("us-set-preset-sleep", sensor_type="air_purifier_us", service_info=AIR_PURIFIER_US_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("us-set-percentage", sensor_type="air_purifier_us", service_info=AIR_PURIFIER_US_SERVICE_INFO, service=SERVICE_SET_PERCENTAGE, service_data={ATTR_PERCENTAGE: 27}, mock_method="set_percentage"),
    test.case("us-turn-off", sensor_type="air_purifier_us", service_info=AIR_PURIFIER_US_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("us-turn-on", sensor_type="air_purifier_us", service_info=AIR_PURIFIER_US_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("table-us-set-preset-sleep", sensor_type="air_purifier_table_us", service_info=AIR_PURIFIER_TABLE_US_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("table-us-set-percentage", sensor_type="air_purifier_table_us", service_info=AIR_PURIFIER_TABLE_US_SERVICE_INFO, service=SERVICE_SET_PERCENTAGE, service_data={ATTR_PERCENTAGE: 27}, mock_method="set_percentage"),
    test.case("table-us-turn-off", sensor_type="air_purifier_table_us", service_info=AIR_PURIFIER_TABLE_US_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("table-us-turn-on", sensor_type="air_purifier_table_us", service_info=AIR_PURIFIER_TABLE_US_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
)
async def air_purifier_controlling(
    sensor_type: str,
    service_info: BluetoothServiceInfoBleak,
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
    """Test controlling the air purifier with different services."""
    inject_bluetooth_service_info(hass, service_info)

    entry = entry_factory(sensor_type)
    entity_id = "fan.test_name"
    entry.add_to_hass(hass)

    mocked_instance = AsyncMock(return_value=True)
    mocked_none_instance = AsyncMock(return_value=None)
    with patch.multiple(
        "homeassistant.components.switchbot.fan.switchbot.SwitchbotAirPurifier",
        get_basic_info=mocked_none_instance,
        update=mocked_none_instance,
        **{mock_method: mocked_instance},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        await hass.services.async_call(
            FAN_DOMAIN,
            service,
            {**service_data, ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mocked_instance.assert_awaited_once()


@test.cases(
    test.case("jp-preset", sensor_type="air_purifier_jp", service_info=AIR_PURIFIER_JP_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("jp-off", sensor_type="air_purifier_jp", service_info=AIR_PURIFIER_JP_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("jp-on", sensor_type="air_purifier_jp", service_info=AIR_PURIFIER_JP_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("table-jp-preset", sensor_type="air_purifier_table_jp", service_info=AIR_PURIFIER_TABLE_JP_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("table-jp-off", sensor_type="air_purifier_table_jp", service_info=AIR_PURIFIER_TABLE_JP_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("table-jp-on", sensor_type="air_purifier_table_jp", service_info=AIR_PURIFIER_TABLE_JP_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("us-preset", sensor_type="air_purifier_us", service_info=AIR_PURIFIER_US_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("us-off", sensor_type="air_purifier_us", service_info=AIR_PURIFIER_US_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("us-on", sensor_type="air_purifier_us", service_info=AIR_PURIFIER_US_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
    test.case("table-us-preset", sensor_type="air_purifier_table_us", service_info=AIR_PURIFIER_TABLE_US_SERVICE_INFO, service=SERVICE_SET_PRESET_MODE, service_data={ATTR_PRESET_MODE: "sleep"}, mock_method="set_preset_mode"),
    test.case("table-us-off", sensor_type="air_purifier_table_us", service_info=AIR_PURIFIER_TABLE_US_SERVICE_INFO, service=SERVICE_TURN_OFF, service_data={}, mock_method="turn_off"),
    test.case("table-us-on", sensor_type="air_purifier_table_us", service_info=AIR_PURIFIER_TABLE_US_SERVICE_INFO, service=SERVICE_TURN_ON, service_data={}, mock_method="turn_on"),
)
async def exception_handling_air_purifier_service(
    sensor_type: str,
    service_info: BluetoothServiceInfoBleak,
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
    """Test exception handling for air purifier service with exception."""
    inject_bluetooth_service_info(hass, service_info)

    entry = entry_factory(sensor_type)
    entry.add_to_hass(hass)
    entity_id = "fan.test_name"

    mocked_none_instance = AsyncMock(return_value=None)
    with patch.multiple(
        "homeassistant.components.switchbot.fan.switchbot.SwitchbotAirPurifier",
        get_basic_info=mocked_none_instance,
        update=mocked_none_instance,
        **{mock_method: AsyncMock(side_effect=SwitchbotOperationError("Operation failed"))},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        raised = False
        try:
            await hass.services.async_call(
                FAN_DOMAIN,
                service,
                {**service_data, ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except HomeAssistantError:
            raised = True
        expect(raised).to_be(True)
