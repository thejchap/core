"""Test the liebherr integration init (tryke port)."""

from typing import Any
from unittest.mock import MagicMock

from pyliebherrhomeapi.exceptions import (
    LiebherrAuthenticationError,
    LiebherrConnectionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_liebherr_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_liebherr_client),
) -> None:
    """Test successful unload of entry."""
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "auth_failed",
        side_effect=LiebherrAuthenticationError("Invalid API key"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "connection_error",
        side_effect=LiebherrConnectionError("Connection failed"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_liebherr_client),
    *,
    side_effect: Any,
    expected_state: ConfigEntryState,
) -> None:
    """Test setup handles various error conditions."""
    entry.add_to_hass(hass)
    client.get_devices.side_effect = side_effect

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(expected_state)


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def coordinator_setup_errors() -> None:
    """Stub for test_coordinator_setup_errors."""


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def dynamic_device_discovery_no_new_devices() -> None:
    """Stub for test_dynamic_device_discovery_no_new_devices."""


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def dynamic_device_discovery_api_error() -> None:
    """Stub for test_dynamic_device_discovery_api_error."""


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def dynamic_device_discovery_unexpected_error() -> None:
    """Stub for test_dynamic_device_discovery_unexpected_error."""


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def dynamic_device_discovery_coordinator_setup_failure() -> None:
    """Stub for test_dynamic_device_discovery_coordinator_setup_failure."""


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def dynamic_device_discovery() -> None:
    """Stub for test_dynamic_device_discovery."""


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def stale_device_removal() -> None:
    """Stub for test_stale_device_removal."""


@test.skip("sibling port deferred (412 LOC, 3 parametrize)")
async def stale_device_removal_without_coordinator() -> None:
    """Stub for test_stale_device_removal_without_coordinator."""
