"""Tryke skip-stubs for test_homeassistant_hardware.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def get_firmware_info_normal() -> None:
    """Stub for test_get_firmware_info_normal."""


@test.skip("zha: sibling test pending tryke port")
async def get_firmware_info_errors() -> None:
    """Stub for test_get_firmware_info_errors."""


@test.skip("zha: sibling test pending tryke port")
async def hardware_firmware_info_provider_notification() -> None:
    """Stub for test_hardware_firmware_info_provider_notification."""
