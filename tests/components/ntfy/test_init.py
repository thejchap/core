"""Tests for the ntfy integration."""

from unittest.mock import AsyncMock

from aiontfy.exceptions import (
    NtfyConnectionError,
    NtfyHTTPError,
    NtfyTimeoutError,
    NtfyUnauthorizedAuthenticationError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import config_entry, mock_aiontfy, mock_random

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _random: object = Depends(mock_random),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def entry_setup_unload(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_aiontfy: AsyncMock = Depends(mock_aiontfy),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test integration setup and unload."""
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "unauthorized",
        exception=NtfyUnauthorizedAuthenticationError(
            40101,
            401,
            "unauthorized",
            "https://ntfy.sh/docs/publish/#authentication",
        ),
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "teapot",
        exception=NtfyHTTPError(418001, 418, "I'm a teapot", ""),
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "connection",
        exception=NtfyConnectionError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "timeout",
        exception=NtfyTimeoutError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def config_entry_not_ready(
    *,
    exception: Exception | type[Exception],
    state: ConfigEntryState,
    hass: HomeAssistant = Depends(_trigger_executor),
    config_entry: MockConfigEntry = Depends(config_entry),
    mock_aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test config entry not ready."""
    mock_aiontfy.account.side_effect = exception
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(state)


@test.cases(
    test.case(
        "unauthorized",
        exception=NtfyUnauthorizedAuthenticationError(
            40101,
            401,
            "unauthorized",
            "https://ntfy.sh/docs/publish/#authentication",
        ),
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "teapot",
        exception=NtfyHTTPError(418001, 418, "I'm a teapot", ""),
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "connection",
        exception=NtfyConnectionError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "timeout",
        exception=NtfyTimeoutError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def coordinator_update_exceptions(
    *,
    exception: Exception | type[Exception],
    state: ConfigEntryState,
    hass: HomeAssistant = Depends(_trigger_executor),
    config_entry: MockConfigEntry = Depends(config_entry),
    mock_aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test config entry not ready from update failed in _async_update_data."""
    mock_aiontfy.account.side_effect = [None, exception]

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(state)
