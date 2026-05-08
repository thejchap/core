"""Tryke skip-stubs for test_lock.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def lock() -> None:
    """Stub for test_lock."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def lock_service_calls() -> None:
    """Stub for test_lock_service_calls."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def lock_service_call_fails() -> None:
    """Stub for test_lock_service_call_fails."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def lock_service_call_fails_with_incorrect_status() -> None:
    """Stub for test_lock_service_call_fails_with_incorrect_status."""
