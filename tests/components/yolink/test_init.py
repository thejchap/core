"""Tryke skip-stubs for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yolink: sibling test pending tryke port")
async def device_remove_devices() -> None:
    """Stub for test_device_remove_devices."""


@test.skip("yolink: sibling test pending tryke port")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""
