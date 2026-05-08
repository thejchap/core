"""Test Scrape component setup process. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup_config() -> None:
    """Stub for test_setup_config (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_no_data_fails_with_recovery() -> None:
    """Stub for test_setup_no_data_fails_with_recovery (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_config_no_configuration() -> None:
    """Stub for test_setup_config_no_configuration (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_config_no_sensors() -> None:
    """Stub for test_setup_config_no_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def device_remove_devices() -> None:
    """Stub for test_device_remove_devices (port deferred)."""

@test.skip("syrupy snapshot")
async def resource_template() -> None:
    """Stub for test_resource_template (port deferred)."""

@test.skip("syrupy snapshot")
async def migrate_from_future() -> None:
    """Stub for test_migrate_from_future (port deferred)."""

@test.skip("syrupy snapshot")
async def migrate_from_version_1_to_2() -> None:
    """Stub for test_migrate_from_version_1_to_2 (port deferred)."""
