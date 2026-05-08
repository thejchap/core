"""Tryke skip-stubs for test_repairs.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def device_config_file_changed_confirm_step() -> None:
    """Stub for test_device_config_file_changed_confirm_step."""


@test.skip("zwave_js: sibling test pending tryke port")
async def device_config_file_changed_cleared() -> None:
    """Stub for test_device_config_file_changed_cleared."""


@test.skip("zwave_js: sibling test pending tryke port")
async def device_config_file_changed_ignore_step() -> None:
    """Stub for test_device_config_file_changed_ignore_step."""


@test.skip("zwave_js: sibling test pending tryke port")
async def invalid_issue() -> None:
    """Stub for test_invalid_issue."""


@test.skip("zwave_js: sibling test pending tryke port")
async def abort_confirm() -> None:
    """Stub for test_abort_confirm."""


@test.skip("zwave_js: sibling test pending tryke port")
async def migrate_unique_id() -> None:
    """Stub for test_migrate_unique_id."""


@test.skip("zwave_js: sibling test pending tryke port")
async def migrate_unique_id_missing_config_entry() -> None:
    """Stub for test_migrate_unique_id_missing_config_entry."""


@test.skip("zwave_js: sibling test pending tryke port")
async def migrate_unique_id_non_integer_ids() -> None:
    """Stub for test_migrate_unique_id_non_integer_ids."""
