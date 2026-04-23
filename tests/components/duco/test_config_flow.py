"""Tests for the Duco config flow."""

from __future__ import annotations

from ipaddress import IPv4Address
from unittest.mock import AsyncMock, MagicMock

from duco.exceptions import DucoConnectionError, DucoError
from tryke import Depends, expect, fixture, test

from homeassistant.components.duco.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.duco._fixtures import (
    TEST_HOST,
    TEST_MAC,
    USER_INPUT,
    mock_config_entry,
    mock_duco_client,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.components.duco._fixtures import (
    mock_board_info as _mock_board_info,
    mock_lan_info as _mock_lan_info,
    mock_nodes as _mock_nodes,
)
from tests.hass_fixtures import hass, mock_network

# Re-export so fixture-chain resolution finds them.
mock_board_info = _mock_board_info
mock_lan_info = _mock_lan_info
mock_nodes = _mock_nodes


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=IPv4Address(TEST_HOST),
    ip_addresses=[IPv4Address(TEST_HOST)],
    port=80,
    hostname="duco_061293.local.",
    type="_http._tcp.local.",
    name="DUCO [a0dd6c061293]._http._tcp.local.",
    properties={},
)


@test
async def user_flow_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_duco_client: AsyncMock = Depends(mock_duco_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("SILENT_CONNECT")
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(TEST_MAC)


@test.cases(
    test.case(
        "connection_error",
        DucoConnectionError("Connection refused"),
        "cannot_connect",
    ),
    test.case("unknown_error", DucoError("Unexpected error"), "unknown"),
)
async def user_flow_error(
    exception: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_duco_client: AsyncMock = Depends(mock_duco_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test handling of connection and unknown errors in the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_duco_client.async_get_board_info.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_duco_client.async_get_board_info.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def user_flow_duplicate(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_duco_client: AsyncMock = Depends(mock_duco_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that a duplicate config entry is aborted."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_discovery_new_device(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_duco_client: AsyncMock = Depends(mock_duco_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery of a new device shows confirmation form and creates entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("SILENT_CONNECT")
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(TEST_MAC)


@test
async def zeroconf_discovery_updates_host(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_duco_client: AsyncMock = Depends(mock_duco_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf discovery updates the host of an existing entry."""
    mock_config_entry.add_to_hass(hass)

    new_ip = "192.168.1.200"
    discovery = ZeroconfServiceInfo(
        ip_address=IPv4Address(new_ip),
        ip_addresses=[IPv4Address(new_ip)],
        port=80,
        hostname="duco_061293.local.",
        type="_http._tcp.local.",
        name="DUCO [a0dd6c061293]._http._tcp.local.",
        properties={},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
    expect(mock_config_entry.data[CONF_HOST]).to_equal(new_ip)


@test
async def zeroconf_discovery_already_configured_same_ip(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_duco_client: AsyncMock = Depends(mock_duco_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf discovery with unchanged IP aborts as already_configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "connection_error",
        DucoConnectionError("Connection refused"),
        "cannot_connect",
    ),
    test.case("unknown_error", DucoError("Unexpected error"), "unknown"),
)
async def zeroconf_discovery_exceptions(
    exception: Exception,
    expected_reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_duco_client: AsyncMock = Depends(mock_duco_client),
) -> None:
    """Test zeroconf discovery aborts on connection and unknown errors."""
    mock_duco_client.async_get_board_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal(expected_reason)
