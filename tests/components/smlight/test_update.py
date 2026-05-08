"""Tests for the SMLIGHT update platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def update_setup() -> None:
    """Stub for test_update_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def update_firmware() -> None:
    """Stub for test_update_firmware (port deferred)."""

@test.skip("syrupy snapshot")
async def update_zigbee2_firmware() -> None:
    """Stub for test_update_zigbee2_firmware (port deferred)."""

@test.skip("syrupy snapshot")
async def update_legacy_firmware_v2() -> None:
    """Stub for test_update_legacy_firmware_v2 (port deferred)."""

@test.skip("syrupy snapshot")
async def update_firmware_failed() -> None:
    """Stub for test_update_firmware_failed (port deferred)."""

@test.skip("syrupy snapshot")
async def update_reboot_timeout() -> None:
    """Stub for test_update_reboot_timeout (port deferred)."""

@test.skip("syrupy snapshot")
async def update_release_notes() -> None:
    """Stub for test_update_release_notes (port deferred)."""

@test.skip("syrupy snapshot")
async def update_blank_release_notes() -> None:
    """Stub for test_update_blank_release_notes (port deferred)."""
