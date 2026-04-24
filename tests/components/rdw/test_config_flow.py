"""Tests for the RDW config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from vehicle.exceptions import RDWConnectionError, RDWUnknownLicensePlateError

from homeassistant.components.rdw.const import CONF_LICENSE_PLATE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_rdw_config_flow as mock_rdw_config_flow_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network + mock_setup_entry for every test."""


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rdw_config_flow: MagicMock = Depends(mock_rdw_config_flow_fx),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LICENSE_PLATE: "11-ZKZ-3"},
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("11-ZKZ-3")
    expect(result2.get("data")).to_equal({CONF_LICENSE_PLATE: "11ZKZ3"})


@test
async def full_flow_with_authentication_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rdw_config_flow: MagicMock = Depends(mock_rdw_config_flow_fx),
) -> None:
    """Test full flow where the user enters an invalid plate then recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    mock_rdw_config_flow.vehicle.side_effect = RDWUnknownLicensePlateError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LICENSE_PLATE: "0001TJ"},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"base": "unknown_license_plate"})

    mock_rdw_config_flow.vehicle.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_LICENSE_PLATE: "11-ZKZ-3"},
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("11-ZKZ-3")
    expect(result3.get("data")).to_equal({CONF_LICENSE_PLATE: "11ZKZ3"})


@test
async def connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rdw_config_flow: MagicMock = Depends(mock_rdw_config_flow_fx),
) -> None:
    """Test API connection error."""
    mock_rdw_config_flow.vehicle.side_effect = RDWConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_LICENSE_PLATE: "0001TJ"},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})
