"""Test the Flexit Nordic (BACnet) config flow."""

import asyncio.exceptions
from unittest.mock import AsyncMock

from flexit_bacnet import DecodingError
from tryke import Depends, expect, fixture, test

from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.flexit_bacnet._fixtures import (
    flow_id,
    mock_config_entry,
    mock_flexit_bacnet,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    flow_id: str = Depends(flow_id),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet),
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
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_flexit_bacnet.mock_calls)).to_equal(1)


@test.cases(
    test.case("timeout", error=asyncio.exceptions.TimeoutError, message="cannot_connect"),
    test.case("connection_error", error=ConnectionError, message="cannot_connect"),
    test.case("decoding_error", error=DecodingError, message="cannot_connect"),
    test.case("unknown", error=Exception(), message="unknown"),
)
async def flow_fails(
    error: type[Exception] | Exception,
    message: str,
    hass: HomeAssistant = Depends(hass_fixture),
    flow_id: str = Depends(flow_id),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet),
) -> None:
    """Test that we return 'cannot_connect' error when connect fails."""
    mock_flexit_bacnet.update.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": message})
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)

    mock_flexit_bacnet.update.side_effect = None
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
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_device_already_exist(
    hass: HomeAssistant = Depends(hass_fixture),
    flow_id: str = Depends(flow_id),
    _mock_flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that we cannot add already added device."""
    mock_config_entry.add_to_hass(hass)

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
