"""Test the Dropbox integration setup."""

from unittest.mock import AsyncMock, patch

from python_dropbox_api import DropboxAuthException, DropboxUnknownException
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)

from ._fixtures import (
    mock_config_entry,
    mock_dropbox_client,
    setup_credentials,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
) -> None:
    """Anchor for tryke fixture resolution + creds."""


@test
async def setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_dropbox_client),
) -> None:
    """Test successful setup of a config entry."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def setup_entry_auth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_dropbox_client),
) -> None:
    """Test setup failure when authentication fails."""
    client.get_account_info.side_effect = DropboxAuthException("Invalid token")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test.cases(
    test.case("unknown_exception", side_effect=DropboxUnknownException("Unknown error")),
    test.case("timeout_error", side_effect=TimeoutError("Connection timed out")),
)
async def setup_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_dropbox_client),
    *,
    side_effect: Exception,
) -> None:
    """Test setup retry when the service is temporarily unavailable."""
    client.get_account_info.side_effect = side_effect
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_entry_implementation_unavailable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup retry when OAuth implementation is unavailable."""
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dropbox.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_dropbox_client),
) -> None:
    """Test unloading a config entry."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
