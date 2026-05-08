"""Tryke skip-stubs for test_select.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def select_params() -> None:
    """Stub for test_select_params."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def select_bad_attr() -> None:
    """Stub for test_select_bad_attr."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def select_option() -> None:
    """Stub for test_select_option."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def select_coordinator_update() -> None:
    """Stub for test_select_coordinator_update."""
