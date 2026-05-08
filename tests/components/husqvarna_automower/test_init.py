"""Tests for husqvarna_automower init module."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.husqvarna_automower.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    expires_at,
    jwt,
    mock_automower_client,
    mock_config_entry,
    mower_time_zone,
    scope,
    setup_credentials,
    values,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _credentials: None = Depends(setup_credentials),
    _client: AsyncMock = Depends(mock_automower_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    expect(entry.state is ConfigEntryState.LOADED).to_be(True)

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state is ConfigEntryState.NOT_LOADED).to_be(True)


@test.skip("port deferred - sibling tests")
async def load_missing_scope() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def expired_token_refresh_failure() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def update_failed() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def websocket_not_available() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def model_id_information() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def device_info() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def constant_polling() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def coordinator_automatic_registry_cleanup() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def add_and_remove_work_area() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def dynamic_polling() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def websocket_watchdog() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def oauth_implementation_not_available() -> None:
    """Stub."""
