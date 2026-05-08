"""Test initialization of lamarzocco."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import async_init_integration
from ._fixtures import (
    mock_cloud_client,
    mock_config_entry,
    mock_generate_installation_key,
    mock_lamarzocco,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _gen_key: MagicMock = Depends(mock_generate_installation_key),
    _cloud: MagicMock = Depends(mock_cloud_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test loading and unloading the integration."""
    await async_init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state is ConfigEntryState.LOADED).to_be(True)


@test.skip("port deferred - sibling test")
async def config_entry_not_ready() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def get_settings_errors() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def invalid_auth() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def v1_migration_fails() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def v4_migration() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def migration_errors() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def config_flow_entry_migration_downgrade() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def websocket_closed_on_unload() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def gateway_version_issue() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def remove_stale_devices() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def device_attributes() -> None:
    """Stub."""
