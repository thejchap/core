"""Test script for Fluss+ integration initialization."""

from unittest.mock import AsyncMock

from fluss_api import (
    FlussApiClientAuthenticationError,
    FlussApiClientCommunicationError,
    FlussApiClientError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_api_client, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_api_client),
) -> None:
    """Test the Fluss configuration entry loading/unloading."""
    await setup_integration(hass, entry)

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(client.async_get_devices.mock_calls)).to_equal(1)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "auth",
        exception=FlussApiClientAuthenticationError,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "comm",
        exception=FlussApiClientCommunicationError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "client",
        exception=FlussApiClientError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def async_setup_entry_authentication_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_api_client),
    *,
    exception: Exception,
    state: ConfigEntryState,
) -> None:
    """Test that an authentication error during setup leads to SETUP_ERROR state."""
    client.async_get_devices.side_effect = exception
    await setup_integration(hass, entry)

    expect(entry.state).to_be(state)


@test.skip("entity_id slug requires translation injection")
async def status_authentication_error_marks_device_offline() -> None:
    """Stub for test_status_authentication_error_marks_device_offline."""
