"""Test the switchbot switches."""

from collections.abc import Callable
from unittest.mock import AsyncMock, patch

from switchbot import SwitchbotOperationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError

from . import (
    PLUG_MINI_EU_SERVICE_INFO,
    RELAY_SWITCH_1_SERVICE_INFO,
    WOHAND_SERVICE_INFO,
    WORELAY_SWITCH_1PM_SERVICE_INFO,
)
from ._fixtures import mock_entry_encrypted_factory, mock_entry_factory

from tests.common import MockConfigEntry, mock_restore_cache
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def switchbot_switch_with_restore_state(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(mock_entry_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that Switchbot Switch restores state correctly after reboot."""
    inject_bluetooth_service_info(hass, WOHAND_SERVICE_INFO)

    entry = entry_factory(sensor_type="bot")
    entity_id = "switch.test_name"

    mock_restore_cache(
        hass,
        [
            State(
                entity_id,
                STATE_ON,
                {"last_run_success": True},
            )
        ],
    )

    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.switchbot.switch.switchbot.Switchbot.switch_mode",
        return_value=False,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes["last_run_success"]).to_be(True)


@test.cases(
    test.case("turn-on", service=SERVICE_TURN_ON, mock_method="turn_on"),
    test.case("turn-off", service=SERVICE_TURN_OFF, mock_method="turn_off"),
)
async def exception_handling_switch(
    service: str,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(mock_entry_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test exception handling for switch service with exception."""
    inject_bluetooth_service_info(hass, WOHAND_SERVICE_INFO)

    entry = entry_factory(sensor_type="bot")
    entry.add_to_hass(hass)
    entity_id = "switch.test_name"

    patch_target = (
        f"homeassistant.components.switchbot.switch.switchbot.Switchbot.{mock_method}"
    )

    with patch(patch_target, new=AsyncMock(side_effect=SwitchbotOperationError("Operation failed"))):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        raised = False
        try:
            await hass.services.async_call(
                SWITCH_DOMAIN,
                service,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except HomeAssistantError:
            raised = True
        expect(raised).to_be(True)


@test.cases(
    test.case("plug_mini_eu-on", sensor_type="plug_mini_eu", service_info=PLUG_MINI_EU_SERVICE_INFO, service=SERVICE_TURN_ON, mock_method="turn_on"),
    test.case("plug_mini_eu-off", sensor_type="plug_mini_eu", service_info=PLUG_MINI_EU_SERVICE_INFO, service=SERVICE_TURN_OFF, mock_method="turn_off"),
    test.case("relay_switch_1-on", sensor_type="relay_switch_1", service_info=RELAY_SWITCH_1_SERVICE_INFO, service=SERVICE_TURN_ON, mock_method="turn_on"),
    test.case("relay_switch_1-off", sensor_type="relay_switch_1", service_info=RELAY_SWITCH_1_SERVICE_INFO, service=SERVICE_TURN_OFF, mock_method="turn_off"),
    test.case("relay_switch_1pm-on", sensor_type="relay_switch_1pm", service_info=WORELAY_SWITCH_1PM_SERVICE_INFO, service=SERVICE_TURN_ON, mock_method="turn_on"),
    test.case("relay_switch_1pm-off", sensor_type="relay_switch_1pm", service_info=WORELAY_SWITCH_1PM_SERVICE_INFO, service=SERVICE_TURN_OFF, mock_method="turn_off"),
)
async def relay_switch_control(
    sensor_type: str,
    service_info: BluetoothServiceInfoBleak,
    service: str,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(
        mock_entry_encrypted_factory
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Relay Switch control."""
    inject_bluetooth_service_info(hass, service_info)

    entry = entry_factory(sensor_type=sensor_type)
    entry.add_to_hass(hass)

    mocked_instance = AsyncMock(return_value=True)
    with patch.multiple(
        "homeassistant.components.switchbot.switch.switchbot.SwitchbotRelaySwitch",
        update=AsyncMock(return_value=None),
        **{mock_method: mocked_instance},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        entity_id = "switch.test_name"

        await hass.services.async_call(
            SWITCH_DOMAIN,
            service,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mocked_instance.assert_awaited_once()


@test.skip("relay_switch_2pm entity_ids (switch.test_name_channel_1/2) need translation injection")
async def relay_switch_2pm_control() -> None:
    """Stub for test_relay_switch_2pm_control (port deferred)."""


@test.cases(
    test.case("relay_switch_1-on", sensor_type="relay_switch_1", service_info=RELAY_SWITCH_1_SERVICE_INFO, entity_id="switch.test_name", mock_class="SwitchbotRelaySwitch", service=SERVICE_TURN_ON, mock_method="turn_on"),
    test.case("relay_switch_1-off", sensor_type="relay_switch_1", service_info=RELAY_SWITCH_1_SERVICE_INFO, entity_id="switch.test_name", mock_class="SwitchbotRelaySwitch", service=SERVICE_TURN_OFF, mock_method="turn_off"),
    test.case("relay_switch_1pm-on", sensor_type="relay_switch_1pm", service_info=WORELAY_SWITCH_1PM_SERVICE_INFO, entity_id="switch.test_name", mock_class="SwitchbotRelaySwitch", service=SERVICE_TURN_ON, mock_method="turn_on"),
    test.case("relay_switch_1pm-off", sensor_type="relay_switch_1pm", service_info=WORELAY_SWITCH_1PM_SERVICE_INFO, entity_id="switch.test_name", mock_class="SwitchbotRelaySwitch", service=SERVICE_TURN_OFF, mock_method="turn_off"),
    test.case("plug_mini_eu-on", sensor_type="plug_mini_eu", service_info=PLUG_MINI_EU_SERVICE_INFO, entity_id="switch.test_name", mock_class="SwitchbotRelaySwitch", service=SERVICE_TURN_ON, mock_method="turn_on"),
    test.case("plug_mini_eu-off", sensor_type="plug_mini_eu", service_info=PLUG_MINI_EU_SERVICE_INFO, entity_id="switch.test_name", mock_class="SwitchbotRelaySwitch", service=SERVICE_TURN_OFF, mock_method="turn_off"),
)
async def relay_switch_control_with_exception(
    sensor_type: str,
    service_info: BluetoothServiceInfoBleak,
    entity_id: str,
    mock_class: str,
    service: str,
    mock_method: str,
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    entry_factory: Callable[[str], MockConfigEntry] = Depends(
        mock_entry_encrypted_factory
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Relay Switch control with exception."""
    inject_bluetooth_service_info(hass, service_info)

    entry = entry_factory(sensor_type=sensor_type)
    entry.add_to_hass(hass)

    with patch.multiple(
        f"homeassistant.components.switchbot.switch.switchbot.{mock_class}",
        update=AsyncMock(return_value=None),
        **{mock_method: AsyncMock(side_effect=SwitchbotOperationError("Operation failed"))},
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        raised = False
        try:
            await hass.services.async_call(
                SWITCH_DOMAIN,
                service,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except HomeAssistantError:
            raised = True
        expect(raised).to_be(True)


@test.skip("air_purifier switch entity_ids (switch.test_name_child_lock) need translation injection")
async def air_purifier_switch_control() -> None:
    """Stub for test_air_purifier_switch_control (port deferred)."""
