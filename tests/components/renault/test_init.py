"""Tests for Renault setup process. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot; indirect parametrize")
async def setup_unload_entry() -> None:
    """Stub for test_setup_unload_entry (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def setup_entry_bad_password() -> None:
    """Stub for test_setup_entry_bad_password (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def setup_entry_exception() -> None:
    """Stub for test_setup_entry_exception (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def setup_entry_kamereon_exception() -> None:
    """Stub for test_setup_entry_kamereon_exception (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def setup_entry_missing_vehicle_details() -> None:
    """Stub for test_setup_entry_missing_vehicle_details (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def device_registry() -> None:
    """Stub for test_device_registry (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def registry_cleanup() -> None:
    """Stub for test_registry_cleanup (port deferred)."""
