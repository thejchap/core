"""Tryke skip-stubs for test_coordinator.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def coordinator_setup_errors() -> None:
    """Stub for test_coordinator_setup_errors."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def coordinator_setup_and_update_errors() -> None:
    """Stub for test_coordinator_setup_and_update_errors."""
