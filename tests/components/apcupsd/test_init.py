"""Test init of APCUPSd integration."""

import asyncio
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.apcupsd.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration, mock_config_entry, mock_request_status

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test.cases(
    test.case("os_error", error=OSError()),
    test.case(
        "incomplete_read",
        error=asyncio.IncompleteReadError(partial=b"", expected=0),
    ),
)
async def connection_error(
    error: Exception,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_request_status: AsyncMock = Depends(mock_request_status),
) -> None:
    """Test connection error during integration setup."""
    mock_config_entry.add_to_hass(hass)
    mock_request_status.side_effect = error

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_remove_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test successful unload and removal of an entry."""
    entry = init_integration
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("entity_id depends on translations not loaded in tryke env")
async def availability() -> None:
    """Stub for test_availability."""
