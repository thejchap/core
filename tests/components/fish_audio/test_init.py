"""Tests for the Fish Audio integration setup."""

from unittest.mock import AsyncMock

from fishaudio import FishAudioError, ServerError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_fishaudio_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_fishaudio_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test entry setup and unload."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("client_error", exception=FishAudioError("Connection error")),
    test.case("server_error", exception=ServerError(500, "Connection error")),
)
async def setup_retry_on_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_fishaudio_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
) -> None:
    """Test entry setup with API errors that should trigger retry."""
    client.account.get_credits.side_effect = exception
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
