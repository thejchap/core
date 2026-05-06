"""Test Droplet config flow."""

from ipaddress import IPv4Address
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.droplet.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import (
    ATTR_CODE,
    CONF_CODE,
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    MOCK_CODE,
    MOCK_DEVICE_ID,
    MOCK_HOST,
    MOCK_PORT,
    mock_config_entry,
    mock_droplet,
    mock_droplet_connection,
    mock_droplet_discovery,
    mock_timeout,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _timeout: None = Depends(mock_timeout),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test.cases(
    test.case(
        "alphanumeric_lower_space",
        pre_normalized_code="abc 123",
        normalized_code="ABC123",
    ),
    test.case(
        "numeric_space", pre_normalized_code=" 123456 ", normalized_code="123456"
    ),
    test.case(
        "alphanumeric_no_space", pre_normalized_code="123ABC", normalized_code="123ABC"
    ),
)
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovery: AsyncMock = Depends(mock_droplet_discovery),
    _connection: AsyncMock = Depends(mock_droplet_connection),
    _droplet: AsyncMock = Depends(mock_droplet),
    *,
    pre_normalized_code: str,
    normalized_code: str,
) -> None:
    """Test successful Droplet user setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: pre_normalized_code, CONF_IP_ADDRESS: "192.168.1.2"},
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("data")).to_equal(
        {
            CONF_CODE: normalized_code,
            CONF_DEVICE_ID: MOCK_DEVICE_ID,
            CONF_IP_ADDRESS: MOCK_HOST,
            CONF_PORT: MOCK_PORT,
        }
    )
    expect(result.get("context") is not None).to_be(True)
    expect(result.get("context", {}).get("unique_id")).to_equal(MOCK_DEVICE_ID)


@test.cases(
    test.case("no_device_id", device_id="", connect_res=True),
    test.case("cannot_connect", device_id=MOCK_DEVICE_ID, connect_res=False),
)
async def user_setup_fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: AsyncMock = Depends(mock_droplet_discovery),
    _connection: AsyncMock = Depends(mock_droplet_connection),
    _droplet: AsyncMock = Depends(mock_droplet),
    *,
    device_id: str,
    connect_res: bool,
) -> None:
    """Test user setup failing due to no device ID or failed connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    attrs = {
        "get_device_id.return_value": device_id,
        "try_connect.return_value": connect_res,
    }
    discovery.configure_mock(**attrs)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE, CONF_IP_ADDRESS: MOCK_HOST},
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})

    attrs = {
        "get_device_id.return_value": MOCK_DEVICE_ID,
        "try_connect.return_value": True,
    }
    discovery.configure_mock(**attrs)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE, CONF_IP_ADDRESS: MOCK_HOST},
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_setup_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _discovery: AsyncMock = Depends(mock_droplet_discovery),
    _droplet: AsyncMock = Depends(mock_droplet),
    _connection: AsyncMock = Depends(mock_droplet_connection),
) -> None:
    """Test user setup of an already-configured device."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE, CONF_IP_ADDRESS: MOCK_HOST},
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test.cases(
    test.case(
        "alphanumeric_lower_space",
        pre_normalized_code="abc 123",
        normalized_code="ABC123",
    ),
    test.case(
        "numeric_space", pre_normalized_code=" 123456 ", normalized_code="123456"
    ),
    test.case(
        "alphanumeric_no_space", pre_normalized_code="123ABC", normalized_code="123ABC"
    ),
)
async def zeroconf_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovery: AsyncMock = Depends(mock_droplet_discovery),
    _droplet: AsyncMock = Depends(mock_droplet),
    _connection: AsyncMock = Depends(mock_droplet_connection),
    *,
    pre_normalized_code: str,
    normalized_code: str,
) -> None:
    """Test successful setup of Droplet via zeroconf."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=IPv4Address(MOCK_HOST),
        ip_addresses=[IPv4Address(MOCK_HOST)],
        port=MOCK_PORT,
        hostname=MOCK_DEVICE_ID,
        type="_droplet._tcp.local.",
        name=MOCK_DEVICE_ID,
        properties={},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_CODE: pre_normalized_code}
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("data")).to_equal(
        {
            CONF_DEVICE_ID: MOCK_DEVICE_ID,
            CONF_IP_ADDRESS: MOCK_HOST,
            CONF_PORT: MOCK_PORT,
            CONF_CODE: normalized_code,
        }
    )
    expect(result.get("context") is not None).to_be(True)
    expect(result.get("context", {}).get("unique_id")).to_equal(MOCK_DEVICE_ID)


@test
async def zeroconf_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    discovery: AsyncMock = Depends(mock_droplet_discovery),
) -> None:
    """Test updating Droplet's host with zeroconf."""
    config_entry.add_to_hass(hass)
    discovery.host = "192.168.1.5"

    new_host = "192.168.1.5"
    expect(config_entry.data[CONF_IP_ADDRESS] != new_host).to_be(True)

    discovery_info = ZeroconfServiceInfo(
        ip_address=IPv4Address(new_host),
        ip_addresses=[IPv4Address(new_host)],
        port=MOCK_PORT,
        hostname=MOCK_DEVICE_ID,
        type="_droplet._tcp.local.",
        name=MOCK_DEVICE_ID,
        properties={},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")

    expect(config_entry.data[CONF_IP_ADDRESS]).to_equal(new_host)


@test
async def zeroconf_invalid_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that invalid discovery information causes the config flow to abort."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=IPv4Address(MOCK_HOST),
        ip_addresses=[IPv4Address(MOCK_HOST)],
        port=-1,
        hostname=MOCK_DEVICE_ID,
        type="_droplet._tcp.local.",
        name=MOCK_DEVICE_ID,
        properties={},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )
    expect(result is not None).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("invalid_discovery_info")


@test
async def confirm_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry: MockConfigEntry = Depends(mock_config_entry),
    _droplet: AsyncMock = Depends(mock_droplet),
    _connection: AsyncMock = Depends(mock_droplet_connection),
    discovery: AsyncMock = Depends(mock_droplet_discovery),
) -> None:
    """Test that config flow fails when Droplet can't connect."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=IPv4Address(MOCK_HOST),
        ip_addresses=[IPv4Address(MOCK_HOST)],
        port=MOCK_PORT,
        hostname=MOCK_DEVICE_ID,
        type="_droplet._tcp.local.",
        name=MOCK_DEVICE_ID,
        properties={},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)

    discovery.try_connect.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {ATTR_CODE: MOCK_CODE}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")["base"]).to_equal("cannot_connect")

    discovery.try_connect.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={ATTR_CODE: MOCK_CODE}
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
