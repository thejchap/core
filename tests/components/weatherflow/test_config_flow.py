"""Tests for WeatherFlow."""

import asyncio
from unittest.mock import AsyncMock, patch

from pyweatherflowudp.errors import AddressInUseError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.weatherflow.const import (
    DOMAIN,
    ERROR_MSG_ADDRESS_IN_USE,
    ERROR_MSG_CANNOT_CONNECT,
    ERROR_MSG_NO_DEVICE_FOUND,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_has_devices,
    mock_setup_entry,
    mock_start,
    mock_stop,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _has_devices: AsyncMock = Depends(mock_has_devices),
) -> None:
    """Test more than one instance."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def devices_with_mocks(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _start: AsyncMock = Depends(mock_start),
    _stop: AsyncMock = Depends(mock_stop),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test getting user input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})


@test.cases(
    test.case(
        "timeout", exception=TimeoutError, error_msg=ERROR_MSG_NO_DEVICE_FOUND
    ),
    test.case(
        "cancelled",
        exception=asyncio.exceptions.CancelledError,
        error_msg=ERROR_MSG_CANNOT_CONNECT,
    ),
    test.case(
        "address_in_use",
        exception=AddressInUseError,
        error_msg=ERROR_MSG_ADDRESS_IN_USE,
    ),
)
async def devices_with_various_mocks_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _start: AsyncMock = Depends(mock_start),
    _stop: AsyncMock = Depends(mock_stop),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: type[Exception],
    error_msg: str,
) -> None:
    """Test the various on error states - then finally complete the test."""
    with patch(
        "homeassistant.components.weatherflow.config_flow.WeatherFlowListener.on",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["base"]).to_equal(error_msg)
        expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})
