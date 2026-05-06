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

from ._fixtures import mock_airthings_token, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_DATA = {
    CONF_ID: "client_id",
    CONF_SECRET: "secret",
}

DHCP_SERVICE_INFO = [
    DhcpServiceInfo(
        hostname="airthings-view",
        ip="192.168.1.100",
        macaddress="000000000000",
    ),
    DhcpServiceInfo(
        hostname="airthings-hub",
        ip="192.168.1.101",
        macaddress="d01411900000",
    ),
    DhcpServiceInfo(
        hostname="airthings-hub",
        ip="192.168.1.102",
        macaddress="70b3d52a0000",
    ),
]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _token: AsyncMock = Depends(mock_airthings_token),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the full flow working."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Airthings")
    expect(result["data"]).to_equal(TEST_DATA)
    expect(result["result"].unique_id).to_equal("client_id")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=airthings.AirthingsAuthError, error="invalid_auth"),
    test.case(
        "cannot_connect",
        exception=airthings.AirthingsConnectionError,
        error="cannot_connect",
    ),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def exceptions(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    token: AsyncMock = Depends(mock_airthings_token),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle exceptions correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    token.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    token.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user input for config_entry that already exists."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("view", dhcp_service_info=DHCP_SERVICE_INFO[0]),
    test.case("hub_d014", dhcp_service_info=DHCP_SERVICE_INFO[1]),
    test.case("hub_70b3", dhcp_service_info=DHCP_SERVICE_INFO[2]),
)
async def dhcp_flow(
    dhcp_service_info: DhcpServiceInfo,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _token: AsyncMock = Depends(mock_airthings_token),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the DHCP discovery flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=dhcp_service_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Airthings")
    expect(result["data"]).to_equal(TEST_DATA)
    expect(result["result"].unique_id).to_equal(TEST_DATA[CONF_ID])
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_flow_hub_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that DHCP discovery fails when already configured."""

    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_SERVICE_INFO[0],
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
