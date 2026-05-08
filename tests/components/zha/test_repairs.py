"""Tryke skip-stubs for test_repairs.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def detect_radio_hardware() -> None:
    """Stub for test_detect_radio_hardware."""


@test.skip("zha: sibling test pending tryke port")
async def detect_radio_hardware_failure() -> None:
    """Stub for test_detect_radio_hardware_failure."""


@test.skip("zha: sibling test pending tryke port")
async def multipan_firmware_repair() -> None:
    """Stub for test_multipan_firmware_repair."""


@test.skip("zha: sibling test pending tryke port")
async def multipan_firmware_no_repair_on_probe_failure() -> None:
    """Stub for test_multipan_firmware_no_repair_on_probe_failure."""


@test.skip("zha: sibling test pending tryke port")
async def multipan_firmware_retry_on_probe_ezsp() -> None:
    """Stub for test_multipan_firmware_retry_on_probe_ezsp."""


@test.skip("zha: sibling test pending tryke port")
async def no_warn_on_socket() -> None:
    """Stub for test_no_warn_on_socket."""


@test.skip("zha: sibling test pending tryke port")
async def inconsistent_settings_keep_new() -> None:
    """Stub for test_inconsistent_settings_keep_new."""


@test.skip("zha: sibling test pending tryke port")
async def inconsistent_settings_restore_old() -> None:
    """Stub for test_inconsistent_settings_restore_old."""
