"""Test the Altruist integration."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_altruist_client,
    mock_altruist_client_fails_once,
    mock_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def setup_entry_client_creation_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client_fails: None = Depends(mock_altruist_client_fails_once),
) -> None:
    """Test setup failure when client creation fails."""
    mock_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
    ).to_be_falsy()
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_entry_fetch_data_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
) -> None:
    """Test setup failure when initial data fetch fails."""
    mock_config_entry.add_to_hass(hass)
    mock_altruist_client.fetch_data.side_effect = Exception("Fetch failed")

    expect(
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
    ).to_be_falsy()
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_altruist_client: AsyncMock = Depends(mock_altruist_client),
) -> None:
    """Test unloading of config entry."""
    mock_config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
