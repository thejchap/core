"""Tests for the seventeentrack service. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def get_packages_from_list() -> None:
    """Stub for test_get_packages_from_list (port deferred)."""

@test.skip("syrupy snapshot")
async def get_all_packages() -> None:
    """Stub for test_get_all_packages (port deferred)."""

@test.skip("syrupy snapshot")
async def service_called_with_unloaded_entry() -> None:
    """Stub for test_service_called_with_unloaded_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def service_called_with_non_17track_device() -> None:
    """Stub for test_service_called_with_non_17track_device (port deferred)."""

@test.skip("syrupy snapshot")
async def archive_package() -> None:
    """Stub for test_archive_package (port deferred)."""

@test.skip("syrupy snapshot")
async def packages_with_none_timestamp() -> None:
    """Stub for test_packages_with_none_timestamp (port deferred)."""
