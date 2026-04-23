"""Test the Airthings config flow."""

from unittest.mock import AsyncMock

import airthings
from tryke import Depends, expect, fixture, test

from homeassistant.components.airthings.const import CONF_SECRET, DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.components.airthings._fixtures import (
    mock_airthings_token,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


TEST_DATA = {
    CONF_ID: "client_id",
    CONF_SECRET: "secret",
}

DHCP_VIEW = DhcpServiceInfo(
    hostname="airthings-view",
    ip="192.168.1.100",
    macaddress="000000000000",
)
DHCP_HUB_1 = DhcpServiceInfo(
    hostname="airthings-hub",
    ip="192.168.1.101",
    macaddress="d01411900000",
)
DHCP_HUB_2 = DhcpServiceInfo(
    hostname="airthings-hub",
    ip="192.168.1.102",
    macaddress="70b3d52a0000",
)


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_airthings_token: AsyncMock = Depends(mock_airthings_token),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the full flow working."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Airthings")
    expect(result["data"]).to_equal(TEST_DATA)
    expect(result["result"].unique_id).to_equal("client_id")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", airthings.AirthingsAuthError, "invalid_auth"),
    test.case("cannot_connect", airthings.AirthingsConnectionError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_airthings_token: AsyncMock = Depends(mock_airthings_token),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle exceptions correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_airthings_token.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": error})

    mock_airthings_token.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def flow_entry_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user input for config_entry that already exists."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"] is None).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("view", DHCP_VIEW),
    test.case("hub_1", DHCP_HUB_1),
    test.case("hub_2", DHCP_HUB_2),
)
async def dhcp_flow(
    dhcp_service_info: DhcpServiceInfo,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_airthings_token: AsyncMock = Depends(mock_airthings_token),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the DHCP discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=dhcp_service_info,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Airthings")
    expect(result["data"]).to_equal(TEST_DATA)
    expect(result["result"].unique_id).to_equal(TEST_DATA[CONF_ID])
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_flow_hub_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that DHCP discovery fails when already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_VIEW,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
