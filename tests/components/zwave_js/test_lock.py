"""Tryke skip-stubs for test_lock.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def door_lock() -> None:
    """Stub for test_door_lock."""


@test.skip("zwave_js: sibling test pending tryke port")
async def only_one_lock() -> None:
    """Stub for test_only_one_lock."""


@test.skip("zwave_js: sibling test pending tryke port")
async def door_lock_no_value() -> None:
    """Stub for test_door_lock_no_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_lock_usercode() -> None:
    """Stub for test_get_lock_usercode."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_lock_usercode_error() -> None:
    """Stub for test_set_lock_usercode_error."""


@test.skip("zwave_js: sibling test pending tryke port")
async def clear_lock_usercode_error() -> None:
    """Stub for test_clear_lock_usercode_error."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_lock_usercode_error() -> None:
    """Stub for test_get_lock_usercode_error."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_all_lock_usercodes() -> None:
    """Stub for test_get_all_lock_usercodes."""
