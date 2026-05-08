"""Tryke skip-stubs for test_update.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def firmware_update_notification_from_zigpy() -> None:
    """Stub for test_firmware_update_notification_from_zigpy."""


@test.skip("zha: sibling test pending tryke port")
async def firmware_update_notification_from_service_call() -> None:
    """Stub for test_firmware_update_notification_from_service_call."""


@test.skip("zha: sibling test pending tryke port")
async def firmware_update_poll_after_reload() -> None:
    """Stub for test_firmware_update_poll_after_reload."""


@test.skip("zha: sibling test pending tryke port")
async def firmware_update_success() -> None:
    """Stub for test_firmware_update_success."""


@test.skip("zha: sibling test pending tryke port")
async def firmware_update_raises() -> None:
    """Stub for test_firmware_update_raises."""


@test.skip("zha: sibling test pending tryke port")
async def update_release_notes() -> None:
    """Stub for test_update_release_notes."""


@test.skip("zha: sibling test pending tryke port")
async def update_version_sync_device_registry() -> None:
    """Stub for test_update_version_sync_device_registry."""
