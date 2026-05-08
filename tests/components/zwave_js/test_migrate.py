"""Tryke skip-stubs for test_migrate.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unique_id_migration_dupes() -> None:
    """Stub for test_unique_id_migration_dupes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unique_id_migration() -> None:
    """Stub for test_unique_id_migration."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unique_id_migration_property_key() -> None:
    """Stub for test_unique_id_migration_property_key."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unique_id_migration_notification_binary_sensor() -> None:
    """Stub for test_unique_id_migration_notification_binary_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def old_entity_migration() -> None:
    """Stub for test_old_entity_migration."""


@test.skip("zwave_js: sibling test pending tryke port")
async def different_endpoint_migration_status_sensor() -> None:
    """Stub for test_different_endpoint_migration_status_sensor."""


@test.skip("zwave_js: sibling test pending tryke port")
async def skip_old_entity_migration_for_multiple() -> None:
    """Stub for test_skip_old_entity_migration_for_multiple."""


@test.skip("zwave_js: sibling test pending tryke port")
async def old_entity_migration_notification_binary_sensor() -> None:
    """Stub for test_old_entity_migration_notification_binary_sensor."""
