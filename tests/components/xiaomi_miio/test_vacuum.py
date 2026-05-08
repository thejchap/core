"""Tryke skip-stubs for test_vacuum.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def xiaomi_exceptions() -> None:
    """Stub for test_xiaomi_exceptions."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def xiaomi_vacuum_services() -> None:
    """Stub for test_xiaomi_vacuum_services."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def xiaomi_specific_services() -> None:
    """Stub for test_xiaomi_specific_services."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def xiaomi_vacuum_fanspeeds() -> None:
    """Stub for test_xiaomi_vacuum_fanspeeds."""
