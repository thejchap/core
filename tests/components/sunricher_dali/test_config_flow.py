"""Test the Sunricher DALI config flow."""

from unittest.mock import AsyncMock, MagicMock

from PySrDaliGateway.exceptions import DaliGatewayError
from tryke import Depends, expect, fixture, test

from homeassistant.components.sunricher_dali.const import CONF_SERIAL_NUMBER, DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_discovery,
    mock_gateway,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def discovery_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    discovery: MagicMock = Depends(mock_discovery),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test a successful discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": gateway.gw_sn},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(gateway.name)
    expect(result.get("data")).to_equal(
        {
            CONF_SERIAL_NUMBER: gateway.gw_sn,
            CONF_HOST: gateway.gw_ip,
            CONF_PORT: gateway.port,
            CONF_NAME: gateway.name,
            CONF_USERNAME: gateway.username,
            CONF_PASSWORD: gateway.passwd,
        }
    )
    result_entry = result.get("result")
    expect(result_entry is not None).to_be(True)
    expect(result_entry.unique_id).to_equal(gateway.gw_sn)
    setup_entry.assert_called_once()
    gateway.connect.assert_awaited_once()
    gateway.disconnect.assert_awaited_once()


@test
async def discovery_no_gateways_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(mock_discovery),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test discovery step when no gateways are found."""
    discovery.discover_gateways.return_value = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")
    errors = result.get("errors")
    expect(errors is not None).to_be(True)
    expect(errors["base"]).to_equal("no_devices_found")

    discovery.discover_gateways.return_value = [gateway]
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": gateway.gw_sn},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def discovery_gateway_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(mock_discovery),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test discovery error handling when gateway search fails."""
    discovery.discover_gateways.side_effect = DaliGatewayError("failure")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")
    errors = result.get("errors")
    expect(errors is not None).to_be(True)
    expect(errors["base"]).to_equal("discovery_failed")

    discovery.discover_gateways.side_effect = None
    discovery.discover_gateways.return_value = [gateway]
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": gateway.gw_sn},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def discovery_connection_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(mock_discovery),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test connection failure when validating the selected gateway."""
    gateway.connect.side_effect = DaliGatewayError("failure")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": gateway.gw_sn},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")
    errors = result.get("errors")
    expect(errors is not None).to_be(True)
    expect(errors["base"]).to_equal("cannot_connect")
    gateway.connect.assert_awaited_once()
    gateway.disconnect.assert_not_awaited()

    gateway.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": gateway.gw_sn},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def discovery_duplicate_filtered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(mock_discovery),
    entry: MockConfigEntry = Depends(mock_config_entry),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test that already configured gateways are filtered out."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")
    errors = result.get("errors")
    expect(errors is not None).to_be(True)
    expect(errors["base"]).to_equal("no_devices_found")

    await hass.config_entries.async_remove(entry.entry_id)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("select_gateway")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": gateway.gw_sn},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def discovery_unique_id_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(mock_discovery),
    entry: MockConfigEntry = Depends(mock_config_entry),
    gateway: MagicMock = Depends(mock_gateway),
) -> None:
    """Test duplicate protection when the entry appears during the flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": gateway.gw_sn},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def dhcp_updates_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test DHCP discovery updates IP of existing entry."""
    entry.add_to_hass(hass)

    expect(entry.data[CONF_HOST] != "192.168.1.200").to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.200",
            macaddress="6a242121110e",
            hostname="dali-gateway",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("192.168.1.200")


@test
async def dhcp_unknown_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery of unknown device aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.100",
            macaddress="aabbccddeeff",
            hostname="unknown-gateway",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("no_dhcp_flow")
