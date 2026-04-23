"""Test the Palazzetti config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pypalazzetti.exceptions import CommunicationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.palazzetti.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_palazzetti_client as mock_palazzetti_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _client: AsyncMock = Depends(mock_palazzetti_client_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire shared fixtures for every test."""


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_palazzetti_client: AsyncMock = Depends(mock_palazzetti_client_fx),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.1"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Stove")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.1"})
    expect(result["result"].unique_id).to_equal("11:22:33:44:55:66")
    expect(len(mock_palazzetti_client.connect.mock_calls) > 0).to_be(True)


@test
async def invalid_host(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_palazzetti_client: AsyncMock = Depends(mock_palazzetti_client_fx),
) -> None:
    """Test cannot connect error."""
    mock_palazzetti_client.connect.side_effect = CommunicationError()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.1"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_palazzetti_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.1"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test duplicate flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.1"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_flow(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the DHCP flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(
            hostname="connbox1234", ip="192.168.1.1", macaddress="112233445566"
        ),
        context={"source": SOURCE_DHCP},
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Stove")
    expect(result["result"].unique_id).to_equal("11:22:33:44:55:66")


@test
async def dhcp_flow_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_palazzetti_client: AsyncMock = Depends(mock_palazzetti_client_fx),
) -> None:
    """Test the DHCP flow with connect error."""
    mock_palazzetti_client.connect.side_effect = CommunicationError()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(
            hostname="connbox1234", ip="192.168.1.1", macaddress="112233445566"
        ),
        context={"source": SOURCE_DHCP},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")
