"""Tryke skip-stubs for test_button.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def vacuum_button_params() -> None:
    """Stub for test_vacuum_button_params."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def vacuum_button_press() -> None:
    """Stub for test_vacuum_button_press."""
