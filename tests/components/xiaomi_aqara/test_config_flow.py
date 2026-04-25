"""Test the Xiaomi Aqara config flow."""

from ipaddress import ip_address
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.xiaomi_aqara import config_flow, const
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT, CONF_PROTOCOL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    TEST_HOST,
    TEST_HOST_2,
    TEST_KEY,
    TEST_MAC,
    TEST_NAME,
    TEST_PORT,
    TEST_PROTOCOL,
    TEST_SID,
    TEST_ZEROCONF_NAME,
    get_mock_discovery,
    xiaomi_aqara,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network

ZEROCONF_MAC = "mac"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _aqara: None = Depends(xiaomi_aqara),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def config_flow_user_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful config flow initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_KEY: TEST_KEY, CONF_NAME: TEST_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PORT: TEST_PORT,
            CONF_MAC: TEST_MAC,
            const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
            CONF_PROTOCOL: TEST_PROTOCOL,
            const.CONF_KEY: TEST_KEY,
            const.CONF_SID: TEST_SID,
        }
    )


@test
async def config_flow_user_multiple_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful config flow initialized by the user with multiple gateways."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_gateway_discovery = get_mock_discovery([TEST_HOST, TEST_HOST_2])

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGatewayDiscovery",
        return_value=mock_gateway_discovery,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("select")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"select_ip": TEST_HOST_2},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_KEY: TEST_KEY, CONF_NAME: TEST_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST_2,
            CONF_PORT: TEST_PORT,
            CONF_MAC: TEST_MAC,
            const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
            CONF_PROTOCOL: TEST_PROTOCOL,
            const.CONF_KEY: TEST_KEY,
            const.CONF_SID: TEST_SID,
        }
    )


@test
async def config_flow_user_no_key_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful config flow initialized by the user without a key."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: TEST_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PORT: TEST_PORT,
            CONF_MAC: TEST_MAC,
            const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
            CONF_PROTOCOL: TEST_PROTOCOL,
            const.CONF_KEY: None,
            const.CONF_SID: TEST_SID,
        }
    )


@test
async def config_flow_user_host_mac_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful config flow with a host and mac specified."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_gateway_discovery = get_mock_discovery([])

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGatewayDiscovery",
        return_value=mock_gateway_discovery,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
                CONF_HOST: TEST_HOST,
                CONF_MAC: TEST_MAC,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: TEST_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PORT: TEST_PORT,
            CONF_MAC: TEST_MAC,
            const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
            CONF_PROTOCOL: TEST_PROTOCOL,
            const.CONF_KEY: None,
            const.CONF_SID: TEST_SID,
        }
    )


@test
async def config_flow_user_discovery_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed config flow with no gateways discovered."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_gateway_discovery = get_mock_discovery([])

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGatewayDiscovery",
        return_value=mock_gateway_discovery,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "discovery_error"})


@test
async def config_flow_user_invalid_interface(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed config flow with an invalid interface."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_gateway_discovery = get_mock_discovery([], invalid_interface=True)

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGatewayDiscovery",
        return_value=mock_gateway_discovery,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({const.CONF_INTERFACE: "invalid_interface"})


@test
async def config_flow_user_invalid_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed config flow with an invalid host."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_gateway_discovery = get_mock_discovery([TEST_HOST], invalid_host=True)

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGateway",
        return_value=mock_gateway_discovery.gateways[TEST_HOST],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
                CONF_HOST: "0.0.0.0",
                CONF_MAC: TEST_MAC,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"host": "invalid_host"})


@test
async def config_flow_user_invalid_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed config flow with an invalid mac."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_gateway_discovery = get_mock_discovery([TEST_HOST], invalid_mac=True)

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGateway",
        return_value=mock_gateway_discovery.gateways[TEST_HOST],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
                CONF_HOST: TEST_HOST,
                CONF_MAC: "in:va:li:d0:0m:ac",
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"mac": "invalid_mac"})


@test
async def config_flow_user_invalid_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed config flow with an invalid key."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_gateway_discovery = get_mock_discovery([TEST_HOST], invalid_key=True)

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGatewayDiscovery",
        return_value=mock_gateway_discovery,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_KEY: TEST_KEY, CONF_NAME: TEST_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")
    expect(result["errors"]).to_equal({const.CONF_KEY: "invalid_key"})


@test
async def zeroconf_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful zeroconf discovery of a xiaomi aqara gateway."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            hostname="mock_hostname",
            name=TEST_ZEROCONF_NAME,
            port=None,
            properties={ZEROCONF_MAC: TEST_MAC},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_KEY: TEST_KEY, CONF_NAME: TEST_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PORT: TEST_PORT,
            CONF_MAC: TEST_MAC,
            const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
            CONF_PROTOCOL: TEST_PROTOCOL,
            const.CONF_KEY: TEST_KEY,
            const.CONF_SID: TEST_SID,
        }
    )


@test
async def zeroconf_missing_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed zeroconf discovery because of missing data."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            hostname="mock_hostname",
            name=TEST_ZEROCONF_NAME,
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_xiaomi_aqara")


@test
async def zeroconf_unknown_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed zeroconf discovery because of an unknown device."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            hostname="mock_hostname",
            name="not-a-xiaomi-aqara-gateway",
            port=None,
            properties={ZEROCONF_MAC: TEST_MAC},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_xiaomi_aqara")
