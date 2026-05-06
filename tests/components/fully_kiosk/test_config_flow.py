"""Test the Fully Kiosk Browser config flow."""

from unittest.mock import AsyncMock, MagicMock, Mock

from aiohttp.client_exceptions import ClientConnectorError
from fullykiosk import FullyKioskError
from tryke import Depends, expect, fixture, test

from homeassistant.components.fully_kiosk.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_MQTT, SOURCE_USER
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_fully_kiosk_config_flow,
    mock_setup_entry,
)

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fk_flow: MagicMock = Depends(mock_fully_kiosk_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user initiated config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Test device")
    expect(result2.get("data")).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_MAC: "aa:bb:cc:dd:ee:ff",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        }
    )
    expect("result" in result2).to_be(True)
    expect(result2["result"].unique_id).to_equal("12345")

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(fk_flow.getDeviceInfo.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "fully_error",
        side_effect=FullyKioskError("error", "status"),
        reason="cannot_connect",
    ),
    test.case(
        "client_connector_error",
        side_effect=ClientConnectorError(None, Mock()),
        reason="cannot_connect",
    ),
    test.case("timeout", side_effect=TimeoutError, reason="cannot_connect"),
    test.case("runtime", side_effect=RuntimeError, reason="unknown"),
)
async def errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fk_flow: MagicMock = Depends(mock_fully_kiosk_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    side_effect: object,
    reason: str,
) -> None:
    """Test errors raised during flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]

    fk_flow.getDeviceInfo.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"base": reason})

    expect(len(fk_flow.getDeviceInfo.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(0)

    fk_flow.getDeviceInfo.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("Test device")
    expect(result3.get("data")).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_MAC: "aa:bb:cc:dd:ee:ff",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        }
    )
    expect("result" in result3).to_be(True)
    expect(result3["result"].unique_id).to_equal("12345")

    expect(len(fk_flow.getDeviceInfo.mock_calls)).to_equal(2)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_updates_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fk_flow: MagicMock = Depends(mock_fully_kiosk_config_flow),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test adding existing device updates existing entry."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("already_configured")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_MAC: "aa:bb:cc:dd:ee:ff",
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        }
    )

    expect(len(fk_flow.getDeviceInfo.mock_calls)).to_equal(1)


@test
async def dhcp_discovery_updates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test DHCP discovery updates config entries."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="tablet",
            ip="127.0.0.2",
            macaddress="aabbccddeeff",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "127.0.0.2",
            CONF_PASSWORD: "mocked-password",
            CONF_MAC: "aa:bb:cc:dd:ee:ff",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        }
    )


@test
async def dhcp_unknown_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test unknown DHCP discovery aborts flow."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="tablet",
            ip="127.0.0.2",
            macaddress="aabbccddee00",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("unknown")


@test
async def mqtt_discovery_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fk_flow: MagicMock = Depends(mock_fully_kiosk_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test MQTT discovery configuration flow."""
    payload = await async_load_fixture(hass, "mqtt-discovery-deviceinfo.json", DOMAIN)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_MQTT},
        data=MqttServiceInfo(
            topic="fully/deviceInfo/e1c9bb1-df31b345",
            payload=payload,
            qos=0,
            retain=False,
            subscribed_topic="fully/deviceInfo/+",
            timestamp=None,
        ),
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("discovery_confirm")

    confirm_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "test-password",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(confirm_result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(confirm_result.get("title")).to_equal("Test device")
    expect(confirm_result.get("data")).to_equal(
        {
            CONF_HOST: "192.168.1.234",
            CONF_PASSWORD: "test-password",
            CONF_MAC: "aa:bb:cc:dd:ee:ff",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        }
    )
    expect("result" in confirm_result).to_be(True)
    expect(confirm_result["result"].unique_id).to_equal("12345")

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(fk_flow.getDeviceInfo.mock_calls)).to_equal(1)


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fk_flow: MagicMock = Depends(mock_fully_kiosk_config_flow),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reconfigure flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "2.2.2.2",
            CONF_PASSWORD: "new-password",
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("2.2.2.2")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")
    expect(config_entry.data[CONF_SSL]).to_be(True)
    expect(config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(fk_flow.getDeviceInfo.mock_calls)).to_equal(1)


@test
async def reconfigure_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fk_flow: MagicMock = Depends(mock_fully_kiosk_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure aborts when device returns a different unique ID."""
    config_entry.add_to_hass(hass)

    fk_flow.getDeviceInfo.return_value = {
        "deviceName": "Other device",
        "deviceID": "67890",
        "Mac": "FF:EE:DD:CC:BB:AA",
    }

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "3.3.3.3",
            CONF_PASSWORD: "other-password",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test.cases(
    test.case(
        "fully_error",
        side_effect=FullyKioskError("error", "status"),
        reason="cannot_connect",
    ),
    test.case(
        "client_connector_error",
        side_effect=ClientConnectorError(None, Mock()),
        reason="cannot_connect",
    ),
    test.case("timeout", side_effect=TimeoutError, reason="cannot_connect"),
    test.case("runtime", side_effect=RuntimeError, reason="unknown"),
)
async def reconfigure_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fk_flow: MagicMock = Depends(mock_fully_kiosk_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    side_effect: object,
    reason: str,
) -> None:
    """Test error handling during reconfigure flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    fk_flow.getDeviceInfo.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "2.2.2.2",
            CONF_PASSWORD: "new-password",
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    # Verify recovery from the error.
    fk_flow.getDeviceInfo.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "2.2.2.2",
            CONF_PASSWORD: "new-password",
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("2.2.2.2")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")
    expect(config_entry.data[CONF_SSL]).to_be(True)
    expect(config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(setup_entry.mock_calls)).to_equal(1)
