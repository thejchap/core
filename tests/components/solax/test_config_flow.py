"""Tests for the solax config flow."""

from __future__ import annotations

from unittest.mock import patch

from solax import RealTimeAPI
from solax.inverter import InverterResponse
from solax.inverters import X1MiniV34
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.solax.const import DOMAIN
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


def _mock_real_time_api_success() -> RealTimeAPI:
    return RealTimeAPI(X1MiniV34)


def _mock_get_data() -> InverterResponse:
    return InverterResponse(
        data=None,
        dongle_serial_number="ABCDEFGHIJ",
        version="2.034.06",
        type=4,
        inverter_serial_number="XXXXXXX",
    )


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful form."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(flow["type"]).to_be(FlowResultType.FORM)
    expect(flow["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.solax.config_flow.real_time_api",
            return_value=_mock_real_time_api_success(),
        ),
        patch("solax.RealTimeAPI.get_data", return_value=_mock_get_data()),
        patch(
            "homeassistant.components.solax.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        entry_result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {CONF_IP_ADDRESS: "192.168.1.87", CONF_PORT: 80, CONF_PASSWORD: "password"},
        )
        await hass.async_block_till_done()

    expect(entry_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry_result["title"]).to_equal("ABCDEFGHIJ")
    expect(entry_result["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "192.168.1.87",
            CONF_PORT: 80,
            CONF_PASSWORD: "password",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_connect_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cannot connect form."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(flow["type"]).to_be(FlowResultType.FORM)
    expect(flow["errors"]).to_equal({})

    with patch(
        "homeassistant.components.solax.config_flow.real_time_api",
        side_effect=ConnectionError,
    ):
        entry_result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {CONF_IP_ADDRESS: "192.168.1.87", CONF_PORT: 80, CONF_PASSWORD: "password"},
        )

    expect(entry_result["type"]).to_be(FlowResultType.FORM)
    expect(entry_result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unknown error form."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(flow["type"]).to_be(FlowResultType.FORM)
    expect(flow["errors"]).to_equal({})

    with patch(
        "homeassistant.components.solax.config_flow.real_time_api",
        side_effect=Exception,
    ):
        entry_result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {CONF_IP_ADDRESS: "192.168.1.87", CONF_PORT: 80, CONF_PASSWORD: "password"},
        )

    expect(entry_result["type"]).to_be(FlowResultType.FORM)
    expect(entry_result["errors"]).to_equal({"base": "unknown"})
