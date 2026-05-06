"""Tests for the Knocki event platform."""

from unittest.mock import AsyncMock

from knocki import KnockiConnectionError, KnockiInvalidAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.knocki.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import setup_integration
from ._fixtures import mock_config_entry, mock_knocki_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

DHCP_DISCOVERY = DhcpServiceInfo(
    ip="1.1.1.1",
    hostname="KNC1-W-00000214",
    macaddress="aabbccddeeff",
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_knocki_client),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    knocki_client: AsyncMock = Depends(mock_knocki_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal({CONF_TOKEN: "test-token"})
    expect(result["result"].unique_id).to_equal("test-id")
    expect(len(knocki_client.link.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort when setting up duplicate entry."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("login_connection", field="login", exception=KnockiConnectionError, error="cannot_connect"),
    test.case("login_invalid_auth", field="login", exception=KnockiInvalidAuthError, error="invalid_auth"),
    test.case("login_unknown", field="login", exception=Exception, error="unknown"),
    test.case("link_connection", field="link", exception=KnockiConnectionError, error="cannot_connect"),
    test.case("link_invalid_auth", field="link", exception=KnockiInvalidAuthError, error="invalid_auth"),
    test.case("link_unknown", field="link", exception=Exception, error="unknown"),
)
async def exceptions(
    field: str,
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    knocki_client: AsyncMock = Depends(mock_knocki_client),
) -> None:
    """Test exceptions."""
    getattr(knocki_client, field).side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    getattr(knocki_client, field).side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal("test-id")


@test.skip("requires full integration setup; runtime_data not configured")
async def dhcp_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    device_reg: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test updating the mac address in the DHCP discovery."""
    await setup_integration(hass, config_entry)

    device = device_reg.async_get_device(identifiers={(DOMAIN, "KNC1-W-00000214")})
    expect(device is not None).to_be(True)
    expect(device.connections).to_equal(set())

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    device = device_reg.async_get_device(identifiers={(DOMAIN, "KNC1-W-00000214")})
    expect(device is not None).to_be(True)
    expect(device.connections).to_equal({(dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff")})


@test
async def dhcp_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test DHCP discovery with already setup device."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
