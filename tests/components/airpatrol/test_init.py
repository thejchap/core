"""Test the AirPatrol integration setup."""

from typing import Any
from unittest.mock import AsyncMock, patch

from airpatrol.api import AirPatrolAuthenticationError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, State

from ._fixtures import get_client, get_data, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def load_unload_config_entry(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    get_client: AsyncMock = Depends(get_client),
) -> None:
    """Test loading and unloading the config entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def update_data_refresh_token_success(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    get_client: AsyncMock = Depends(get_client),
    get_data: list[dict[str, Any]] = Depends(get_data),
) -> None:
    """Test data update with expired token and successful token refresh."""
    get_client.get_data.side_effect = [
        AirPatrolAuthenticationError("fail"),
        get_data,
    ]

    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(get_client.get_data.call_count).to_equal(2)
    expect(hass.states.get("climate.living_room")).not_.to_be(None)


@test
async def update_data_auth_failure(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    get_client: AsyncMock = Depends(get_client),
) -> None:
    """Test permanent authentication failure."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.airpatrol.coordinator.AirPatrolAPI.authenticate",
        side_effect=AirPatrolAuthenticationError("fail"),
    ):
        get_client.get_data.side_effect = AirPatrolAuthenticationError("fail")

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state: State | None = hass.states.get("climate.living_room")
        expect(state).to_be(None)

        entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
        expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
        expect(entry.reason).to_equal("Authentication with AirPatrol failed")
