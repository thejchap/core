"""Test the Pure Energie config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import MagicMock

from gridnet import GridNetConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.pure_energie.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_pure_energie_config_flow as mock_pure_energie_config_flow_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
) -> None:
    """Wire mock_network + zeroconf for every test."""


@test
async def full_user_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_client: MagicMock = Depends(mock_pure_energie_config_flow_fx),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
    )

    expect(result.get("title")).to_equal("Pure Energie Meter")
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("aabbccddeeff")


@test
async def full_zeroconf_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_client: MagicMock = Depends(mock_pure_energie_config_flow_fx),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full zeroconf flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "aabbccddeeff"},
            type="mock_type",
        ),
    )

    expect(result.get("description_placeholders")).to_equal(
        {
            "model": "SBWF3102",
            CONF_NAME: "Pure Energie Meter",
        }
    )
    expect(result.get("step_id")).to_equal("zeroconf_confirm")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result2.get("title")).to_equal("Pure Energie Meter")
    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result2).to_be(True)
    expect(result2["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect("result" in result2).to_be(True)
    expect(result2["result"].unique_id).to_equal("aabbccddeeff")


@test
async def connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pure_energie_config_flow: MagicMock = Depends(
        mock_pure_energie_config_flow_fx
    ),
) -> None:
    """Test we show user form on Pure Energie connection error."""
    mock_pure_energie_config_flow.device.side_effect = GridNetConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "example.com"},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})


@test
async def zeroconf_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pure_energie_config_flow: MagicMock = Depends(
        mock_pure_energie_config_flow_fx
    ),
) -> None:
    """Test we abort zeroconf flow on Pure Energie connection error."""
    mock_pure_energie_config_flow.device.side_effect = GridNetConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "aabbccddeeff"},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")
