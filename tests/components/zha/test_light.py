"""Tryke skip-stubs for test_light.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def light() -> None:
    """Stub for test_light."""


@test.skip("zha: sibling test pending tryke port")
async def on_with_off_color() -> None:
    """Stub for test_on_with_off_color."""


@test.skip("zha: sibling test pending tryke port")
async def light_exception_on_creation() -> None:
    """Stub for test_light_exception_on_creation."""
