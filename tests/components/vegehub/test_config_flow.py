"""Tests for VegeHub config flow."""

from ipaddress import ip_address
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.vegehub.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import (
    CONF_DEVICE,
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_WEBHOOK_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import (
    ATTR_PROPERTIES_ID,
    ZeroconfServiceInfo,
)

from ._fixtures import (
    TEST_HOSTNAME,
    TEST_IP,
    TEST_SIMPLE_MAC,
    mock_setup_entry,
    mock_vegehub,
    mocked_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address(TEST_IP),
    ip_addresses=[ip_address(TEST_IP)],
    port=80,
    hostname=f"{TEST_HOSTNAME}.local.",
    type="mock_type",
    name="myVege",
    properties={
        ATTR_PROPERTIES_ID: TEST_HOSTNAME,
        "version": "5.1.1",
    },
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _vegehub: MagicMock = Depends(mock_vegehub),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow with successful configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_IP)
    expect(result["data"][CONF_MAC]).to_equal(TEST_SIMPLE_MAC)
    expect(result["data"][CONF_IP_ADDRESS]).to_equal(TEST_IP)
    expect(result["data"][CONF_DEVICE] is not None).to_be(True)
    expect(result["data"][CONF_WEBHOOK_ID] is not None).to_be(True)

    expect(result["data"][CONF_HOST]).to_equal(TEST_IP)
    expect(result["result"].unique_id).to_equal(TEST_SIMPLE_MAC)

    entries = hass.config_entries.async_entries(domain=DOMAIN)
    expect(len(entries)).to_equal(1)


@test
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vegehub: MagicMock = Depends(mock_vegehub),
) -> None:
    """Test the user flow with bad data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    vegehub.mac_address = ""

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("cannot_connect")

    vegehub.mac_address = TEST_SIMPLE_MAC

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case(
        "timeout", side_effect=TimeoutError, expected_error="timeout_connect"
    ),
    test.case(
        "connection_error",
        side_effect=ConnectionError,
        expected_error="cannot_connect",
    ),
)
async def user_flow_device_bad_connection_then_success(
    *,
    side_effect: type[Exception],
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vegehub: MagicMock = Depends(mock_vegehub),
) -> None:
    """Test the user flow with a timeout."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    vegehub.setup.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("errors" in result).to_be(True)
    expect(result["errors"]).to_equal({"base": expected_error})

    vegehub.setup.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_IP)
    expect(result["data"][CONF_IP_ADDRESS]).to_equal(TEST_IP)
    expect(result["data"][CONF_MAC]).to_equal(TEST_SIMPLE_MAC)


@test
async def user_flow_no_ip_entered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow with blank IP."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: ""}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_ip")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_bad_ip_entered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow with badly formed IP."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: "192.168.0"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_ip")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_duplicate_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mocked_config_entry),
) -> None:
    """Test when user flow gets the same device twice."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def zeroconf_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the zeroconf discovery flow with successful configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], None)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_HOSTNAME)
    expect(result["data"][CONF_HOST]).to_equal(TEST_HOSTNAME)
    expect(result["data"][CONF_MAC]).to_equal(TEST_SIMPLE_MAC)
    expect(result["result"].unique_id).to_equal(TEST_SIMPLE_MAC)


@test
async def zeroconf_flow_abort_device_asleep(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vegehub: MagicMock = Depends(mock_vegehub),
) -> None:
    """Test when zeroconf tries to contact a device that is asleep."""
    vegehub.retrieve_mac_address.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("timeout_connect")


@test
async def zeroconf_flow_abort_same_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mocked_config_entry),
) -> None:
    """Test when zeroconf gets the same device twice."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def zeroconf_flow_abort_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vegehub: MagicMock = Depends(mock_vegehub),
) -> None:
    """Test when zeroconf gets bad data."""
    vegehub.mac_address = ""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def zeroconf_flow_abort_cannot_connect_404(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vegehub: MagicMock = Depends(mock_vegehub),
) -> None:
    """Test when zeroconf gets bad responses."""
    vegehub.retrieve_mac_address.side_effect = ConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test.cases(
    test.case("timeout", side_effect=TimeoutError, expected_error="timeout_connect"),
    test.case(
        "connection_error",
        side_effect=ConnectionError,
        expected_error="cannot_connect",
    ),
)
async def zeroconf_flow_device_error_response(
    *,
    side_effect: type[Exception],
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vegehub: MagicMock = Depends(mock_vegehub),
) -> None:
    """Test when zeroconf detects the device, but the communication fails at setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")

    vegehub.setup.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)

    vegehub.setup.side_effect = None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf_flow_update_ip_hostname(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mocked_config_entry),
) -> None:
    """Test when zeroconf gets the same device with a new IP and hostname."""
    config_entry.add_to_hass(hass)

    new_ip = "192.168.0.99"
    new_hostname = "new_hostname"
    new_discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address(new_ip),
        ip_addresses=[ip_address(new_ip)],
        port=DISCOVERY_INFO.port,
        hostname=f"{new_hostname}.local.",
        type=DISCOVERY_INFO.type,
        name=DISCOVERY_INFO.name,
        properties=DISCOVERY_INFO.properties,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=new_discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)

    entries = hass.config_entries.async_entries(domain=DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(config_entry.data[CONF_IP_ADDRESS]).to_equal(new_ip)
    expect(config_entry.data[CONF_HOST]).to_equal(new_hostname)
