"""Test the Fjäråskupan config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.fjaraskupan.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import COOKER_SERVICE_INFO
from ._fixtures import mock_setup_entry

from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def configure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    with patch(
        "homeassistant.components.fjaraskupan.config_flow.async_discovered_service_info",
        return_value=[COOKER_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Fjäråskupan")
        expect(result["data"]).to_equal({})

        await hass.async_block_till_done()
        expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def scan_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""

    with patch(
        "homeassistant.components.fjaraskupan.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_devices_found")
