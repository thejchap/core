"""Tryke skip-stubs for test_image.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xbox: sibling test pending tryke port")
async def image_platform() -> None:
    """Stub for test_image_platform."""


@test.skip("xbox: sibling test pending tryke port")
async def load_image_from_url() -> None:
    """Stub for test_load_image_from_url."""
