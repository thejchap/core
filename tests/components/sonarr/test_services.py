"""Tests for Sonarr services."""

from unittest.mock import MagicMock

from aiopyarr.exceptions import ArrAuthenticationException, ArrConnectionException
from tryke import Depends, expect, fixture, test

from homeassistant.components.sonarr.const import (
    ATTR_ENTRY_ID,
    DOMAIN,
    SERVICE_GET_DISKSPACE,
    SERVICE_GET_QUEUE,
    SERVICE_GET_SERIES,
    SERVICE_GET_UPCOMING,
    SERVICE_GET_WANTED,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from ._fixtures import init_integration, mock_sonarr

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

@test.cases(
    test.case("get_series", service=SERVICE_GET_SERIES),
    test.case("get_queue", service=SERVICE_GET_QUEUE),
    test.case("get_diskspace", service=SERVICE_GET_DISKSPACE),
    test.case("get_upcoming", service=SERVICE_GET_UPCOMING),
    test.case("get_wanted", service=SERVICE_GET_WANTED),
)
async def services_entry_not_loaded(
    service: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test services with unloaded config entry."""
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            service,
            {ATTR_ENTRY_ID: entry.entry_id},
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be(None)
    expect(raised.translation_key).to_equal("not_loaded")

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

@test.cases(
    test.case(
        "get_series",
        service=SERVICE_GET_SERIES,
        method="async_get_series",
    ),
    test.case(
        "get_queue",
        service=SERVICE_GET_QUEUE,
        method="async_get_queue",
    ),
    test.case(
        "get_diskspace",
        service=SERVICE_GET_DISKSPACE,
        method="async_get_diskspace",
    ),
    test.case(
        "get_upcoming",
        service=SERVICE_GET_UPCOMING,
        method="async_get_calendar",
    ),
    test.case(
        "get_wanted",
        service=SERVICE_GET_WANTED,
        method="async_get_wanted",
    ),
)
async def services_api_connection_error(
    service: str,
    method: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
    sonarr: MagicMock = Depends(mock_sonarr),
) -> None:
    """Test services with API connection error."""
    getattr(sonarr, method).side_effect = ArrConnectionException("Connection failed")

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            service,
            {ATTR_ENTRY_ID: entry.entry_id},
            blocking=True,
            return_response=True,
        )


@test.cases(
    test.case(
        "get_series",
        service=SERVICE_GET_SERIES,
        method="async_get_series",
    ),
    test.case(
        "get_queue",
        service=SERVICE_GET_QUEUE,
        method="async_get_queue",
    ),
    test.case(
        "get_diskspace",
        service=SERVICE_GET_DISKSPACE,
        method="async_get_diskspace",
    ),
    test.case(
        "get_upcoming",
        service=SERVICE_GET_UPCOMING,
        method="async_get_calendar",
    ),
    test.case(
        "get_wanted",
        service=SERVICE_GET_WANTED,
        method="async_get_wanted",
    ),
)
async def services_api_auth_error(
    service: str,
    method: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
    sonarr: MagicMock = Depends(mock_sonarr),
) -> None:
    """Test services with API authentication error."""
    getattr(sonarr, method).side_effect = ArrAuthenticationException(
        "Authentication failed"
    )

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            service,
            {ATTR_ENTRY_ID: entry.entry_id},
            blocking=True,
            return_response=True,
        )
