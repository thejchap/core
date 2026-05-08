"""Tryke skip-stubs for test_update.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_states() -> None:
    """Stub for test_update_entity_states."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_install_raises() -> None:
    """Stub for test_update_entity_install_raises."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_sleep() -> None:
    """Stub for test_update_entity_sleep."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_dead() -> None:
    """Stub for test_update_entity_dead."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_ha_not_running() -> None:
    """Stub for test_update_entity_ha_not_running."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_update_failure() -> None:
    """Stub for test_update_entity_update_failure."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_progress() -> None:
    """Stub for test_update_entity_progress."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_install_failed() -> None:
    """Stub for test_update_entity_install_failed."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_reload() -> None:
    """Stub for test_update_entity_reload."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_delay() -> None:
    """Stub for test_update_entity_delay."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_partial_restore_data() -> None:
    """Stub for test_update_entity_partial_restore_data."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_partial_restore_data_2() -> None:
    """Stub for test_update_entity_partial_restore_data_2."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_full_restore_data_skipped_version() -> None:
    """Stub for test_update_entity_full_restore_data_skipped_version."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_full_restore_data_update_available() -> None:
    """Stub for test_update_entity_full_restore_data_update_available."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_full_restore_data_no_update_available() -> None:
    """Stub for test_update_entity_full_restore_data_no_update_available."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_entity_no_latest_version() -> None:
    """Stub for test_update_entity_no_latest_version."""
