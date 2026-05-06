"""Test the Flexit Nordic (BACnet) config flow."""

import asyncio.exceptions
from unittest.mock import AsyncMock

from flexit_bacnet import DecodingError
from tryke import Depends, expect, fixture, test

from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    flow_id,
    mock_config_entry,
    mock_flexit_bacnet,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    flow_id: str = Depends(flow_id),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet),
) -> None:
    """Test we get the form and the happy path works."""
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Device Name")
    expect(result["context"]["unique_id"]).to_equal("0000-0001")
    expect(result["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(flexit_bacnet.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "timeout", error=asyncio.exceptions.TimeoutError, message="cannot_connect"
    ),
    test.case("conn_err", error=ConnectionError, message="cannot_connect"),
    test.case("decode_err", error=DecodingError, message="cannot_connect"),
    test.case("unknown", error=Exception(), message="unknown"),
)
async def flow_fails(
    error: Exception,
    message: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    flow_id: str = Depends(flow_id),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet),
) -> None:
    """Test that we return errors when attempting to connect."""
    flexit_bacnet.update.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": message})
    expect(len(setup_entry.mock_calls)).to_equal(0)

    flexit_bacnet.update.side_effect = None
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Device Name")
    expect(result2["context"]["unique_id"]).to_equal("0000-0001")
    expect(result2["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_device_already_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    flow_id: str = Depends(flow_id),
    _flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that we cannot add already added device."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
