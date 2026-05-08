"""Tryke skip-stubs for test_event.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def basic() -> None:
    """Stub for test_basic."""


@test.skip("zwave_js: sibling test pending tryke port")
async def central_scene() -> None:
    """Stub for test_central_scene."""
