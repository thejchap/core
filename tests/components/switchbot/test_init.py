"""Test the switchbot init. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def exception_handling_for_device_initialization() -> None:
    """Stub for test_exception_handling_for_device_initialization (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_without_ble_device() -> None:
    """Stub for test_setup_entry_without_ble_device (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_meter_pro_co2_uses_non_connectable() -> None:
    """Stub for test_setup_entry_meter_pro_co2_uses_non_connectable (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_wait_ready_timeout() -> None:
    """Stub for test_coordinator_wait_ready_timeout (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_entry_from_v1_1_to_v1_2() -> None:
    """Stub for test_migrate_entry_from_v1_1_to_v1_2 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_entry_preserves_existing_options() -> None:
    """Stub for test_migrate_entry_preserves_existing_options (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_entry_fails_for_future_version() -> None:
    """Stub for test_migrate_entry_fails_for_future_version (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_deprecated_air_purifier_sensor_type() -> None:
    """Stub for test_migrate_deprecated_air_purifier_sensor_type (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_deprecated_air_purifier_sensor_type_device_not_in_range() -> None:
    """Stub for test_migrate_deprecated_air_purifier_sensor_type_device_not_in_range (port deferred)."""
