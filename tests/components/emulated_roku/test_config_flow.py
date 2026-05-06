"""Tests for emulated_roku config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.emulated_roku import config_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"name": "Emulated Roku Test", "listen_port": 8060},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Emulated Roku Test")
    expect(result["data"]).to_equal({"name": "Emulated Roku Test", "listen_port": 8060})


@test
async def flow_already_registered_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow doesn't allow existing names."""
    MockConfigEntry(
        domain="emulated_roku", data={"name": "Emulated Roku Test", "listen_port": 8062}
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"name": "Emulated Roku Test", "listen_port": 8062},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
