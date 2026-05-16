"""Tests for the Concord232 alarm control panel platform."""

from unittest.mock import MagicMock

from freezegun.api import FrozenDateTimeFactory
import requests
from tryke import Depends, expect, fixture, test

from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_DISARM,
    AlarmControlPanelState,
)
from homeassistant.const import (
    ATTR_CODE,
    ATTR_ENTITY_ID,
    CONF_CODE,
    CONF_HOST,
    CONF_MODE,
    CONF_NAME,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import _trigger_executor, mock_concord232_client

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
)

VALID_CONFIG = {
    ALARM_DOMAIN: {
        "platform": "concord232",
        CONF_HOST: "localhost",
        CONF_PORT: 5007,
        CONF_NAME: "Test Alarm",
    }
}

VALID_CONFIG_WITH_CODE = {
    ALARM_DOMAIN: {
        "platform": "concord232",
        CONF_HOST: "localhost",
        CONF_PORT: 5007,
        CONF_NAME: "Test Alarm",
        CONF_CODE: "1234",
    }
}

VALID_CONFIG_SILENT_MODE = {
    ALARM_DOMAIN: {
        "platform": "concord232",
        CONF_HOST: "localhost",
        CONF_PORT: 5007,
        CONF_NAME: "Test Alarm",
        CONF_MODE: "silent",
    }
}


@fixture
def _setup_trigger(_t: int = Depends(_trigger_executor)) -> int:
    """Ensure _trigger_executor fixture is resolved (anchored to module)."""
    return _t


@test
async def setup_platform(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
) -> None:
    """Test platform setup."""
    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()

    state = hass.states.get("alarm_control_panel.test_alarm")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(AlarmControlPanelState.DISARMED)


@test
async def setup_platform_connection_error(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
) -> None:
    """Test platform setup with connection error."""
    mock_concord232_client.list_partitions.side_effect = (
        requests.exceptions.ConnectionError("Connection failed")
    )

    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()

    expect(hass.states.get("alarm_control_panel.test_alarm")).to_be_none()


@test
async def alarm_disarm(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
) -> None:
    """Test disarm service."""
    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: "alarm_control_panel.test_alarm"},
        blocking=True,
    )
    mock_concord232_client.disarm.assert_called_once_with(None)


@test
async def alarm_disarm_with_code(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
) -> None:
    """Test disarm service with code."""
    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG_WITH_CODE)
    await hass.async_block_till_done()

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {
            ATTR_ENTITY_ID: "alarm_control_panel.test_alarm",
            ATTR_CODE: "1234",
        },
        blocking=True,
    )
    mock_concord232_client.disarm.assert_called_once_with("1234")


@test
async def alarm_disarm_invalid_code(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test disarm service with invalid code."""
    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG_WITH_CODE)
    await hass.async_block_till_done()

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {
            ATTR_ENTITY_ID: "alarm_control_panel.test_alarm",
            ATTR_CODE: "9999",
        },
        blocking=True,
    )
    mock_concord232_client.disarm.assert_not_called()
    expect("Invalid code given" in caplog.text).to_be(True)


@test.cases(
    test.case("arm_home", service=SERVICE_ALARM_ARM_HOME, expected_arm_call="stay"),
    test.case("arm_away", service=SERVICE_ALARM_ARM_AWAY, expected_arm_call="away"),
)
async def alarm_arm(
    service: str,
    expected_arm_call: str,
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
) -> None:
    """Test arm service."""
    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG_WITH_CODE)
    await hass.async_block_till_done()

    await hass.services.async_call(
        ALARM_DOMAIN,
        service,
        {
            ATTR_ENTITY_ID: "alarm_control_panel.test_alarm",
            ATTR_CODE: "1234",
        },
        blocking=True,
    )
    mock_concord232_client.arm.assert_called_once_with(expected_arm_call)


@test
async def alarm_arm_home_silent_mode(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
) -> None:
    """Test arm home service with silent mode."""
    config_with_code = VALID_CONFIG_SILENT_MODE.copy()
    config_with_code[ALARM_DOMAIN][CONF_CODE] = "1234"
    await async_setup_component(hass, ALARM_DOMAIN, config_with_code)
    await hass.async_block_till_done()

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_HOME,
        {
            ATTR_ENTITY_ID: "alarm_control_panel.test_alarm",
            ATTR_CODE: "1234",
        },
        blocking=True,
    )
    mock_concord232_client.arm.assert_called_once_with("stay", "silent")


@test
async def update_state_disarmed(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
) -> None:
    """Test update when alarm is disarmed."""
    mock_concord232_client.list_partitions.return_value = [{"arming_level": "Off"}]
    mock_concord232_client.list_zones.return_value = [
        {"number": 1, "name": "Zone 1", "state": "Normal"},
    ]

    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()

    state = hass.states.get("alarm_control_panel.test_alarm")
    expect(state.state).to_equal(AlarmControlPanelState.DISARMED)


@test.cases(
    test.case("home", arming_level="Home", expected_state=AlarmControlPanelState.ARMED_HOME),
    test.case("away", arming_level="Away", expected_state=AlarmControlPanelState.ARMED_AWAY),
)
async def update_state_armed(
    arming_level: str,
    expected_state: str,
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test update when alarm is armed."""
    mock_concord232_client.list_partitions.return_value = [
        {"arming_level": arming_level}
    ]
    mock_concord232_client.partitions = (
        mock_concord232_client.list_partitions.return_value
    )
    mock_concord232_client.list_zones.return_value = [
        {"number": 1, "name": "Zone 1", "state": "Normal"},
    ]

    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()

    freezer.tick(10)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("alarm_control_panel.test_alarm")
    expect(state.state).to_equal(expected_state)


@test
async def update_connection_error(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test update with connection error."""
    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()

    mock_concord232_client.list_partitions.side_effect = (
        requests.exceptions.ConnectionError("Connection failed")
    )

    freezer.tick(10)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect("Unable to connect to" in caplog.text).to_be(True)


@test
async def update_no_partitions(
    _t: int = Depends(_setup_trigger),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_concord232_client: MagicMock = Depends(mock_concord232_client),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test update when no partitions are available."""
    mock_concord232_client.list_partitions.return_value = []

    await async_setup_component(hass, ALARM_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()

    expect("Concord232 reports no partitions" in caplog.text).to_be(True)
