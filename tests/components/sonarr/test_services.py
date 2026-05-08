"""Tests for Sonarr services."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.sonarr.const import (
    ATTR_ENTRY_ID,
    DOMAIN,
    SERVICE_GET_SERIES,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from ._fixtures import init_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def services_integration_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test service call with non-existent config entry raises."""
    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_SERIES,
            {ATTR_ENTRY_ID: "non_existent_entry_id"},
            blocking=True,
            return_response=True,
        )


@test
async def services_config_entry_not_loaded_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test service call when config entry is in failed state."""
    unloaded_entry = MockConfigEntry(
        title="Sonarr",
        domain=DOMAIN,
        unique_id="unloaded",
    )
    unloaded_entry.add_to_hass(hass)

    expect(unloaded_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_SERIES,
            {ATTR_ENTRY_ID: unloaded_entry.entry_id},
            blocking=True,
            return_response=True,
        )


@test.skip("requires syrupy snapshot")
async def service_get_series() -> None:
    """Stub for test_service_get_series (port deferred)."""

@test.skip("requires syrupy snapshot")
async def service_get_queue() -> None:
    """Stub for test_service_get_queue (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def services_entry_not_loaded() -> None:
    """Stub for test_services_entry_not_loaded (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_queue_empty() -> None:
    """Stub for test_service_get_queue_empty (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_diskspace() -> None:
    """Stub for test_service_get_diskspace (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_diskspace_multiple_drives() -> None:
    """Stub (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_upcoming() -> None:
    """Stub (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_wanted() -> None:
    """Stub (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_episodes() -> None:
    """Stub (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_episodes_with_season_filter() -> None:
    """Stub (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_queue_image_fallback() -> None:
    """Stub (port deferred)."""

@test.skip("requires mock state injection")
async def service_get_queue_season_pack() -> None:
    """Stub (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def services_api_connection_error() -> None:
    """Stub (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def services_api_auth_error() -> None:
    """Stub (port deferred)."""
