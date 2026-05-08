"""Tryke skip-stubs for test_entity.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def device_registry_via_device() -> None:
    """Stub for test_device_registry_via_device."""
