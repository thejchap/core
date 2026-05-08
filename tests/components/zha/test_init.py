"""Tryke skip-stubs for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def migration_from_v1_no_baudrate() -> None:
    """Stub for test_migration_from_v1_no_baudrate."""


@test.skip("zha: sibling test pending tryke port")
async def migration_from_v1_with_baudrate() -> None:
    """Stub for test_migration_from_v1_with_baudrate."""


@test.skip("zha: sibling test pending tryke port")
async def migration_from_v1_wrong_baudrate() -> None:
    """Stub for test_migration_from_v1_wrong_baudrate."""


@test.skip("zha: sibling test pending tryke port")
async def config_depreciation() -> None:
    """Stub for test_config_depreciation."""


@test.skip("zha: sibling test pending tryke port")
async def setup_with_v3_cleaning_uri() -> None:
    """Stub for test_setup_with_v3_cleaning_uri."""


@test.skip("zha: sibling test pending tryke port")
async def migration_baudrate_and_flow_control() -> None:
    """Stub for test_migration_baudrate_and_flow_control."""


@test.skip("zha: sibling test pending tryke port")
async def zha_retry_unique_ids() -> None:
    """Stub for test_zha_retry_unique_ids."""


@test.skip("zha: sibling test pending tryke port")
async def shutdown_on_ha_stop() -> None:
    """Stub for test_shutdown_on_ha_stop."""


@test.skip("zha: sibling test pending tryke port")
async def timezone_update() -> None:
    """Stub for test_timezone_update."""


@test.skip("zha: sibling test pending tryke port")
async def setup_no_firmware_update_in_progress() -> None:
    """Stub for test_setup_no_firmware_update_in_progress."""


@test.skip("zha: sibling test pending tryke port")
async def setup_firmware_update_in_progress() -> None:
    """Stub for test_setup_firmware_update_in_progress."""


@test.skip("zha: sibling test pending tryke port")
async def setup_firmware_update_in_progress_prevents_silabs_warning() -> None:
    """Stub for test_setup_firmware_update_in_progress_prevents_silabs_warning."""


@test.skip("zha: sibling test pending tryke port")
async def device_path_migration_to_unique_path() -> None:
    """Stub for test_device_path_migration_to_unique_path."""


@test.skip("zha: sibling test pending tryke port")
async def device_path_not_changed_when_already_unique() -> None:
    """Stub for test_device_path_not_changed_when_already_unique."""


@test.skip("zha: sibling test pending tryke port")
async def gateway_created_with_migrated_device_path() -> None:
    """Stub for test_gateway_created_with_migrated_device_path."""
