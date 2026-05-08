"""Tryke skip stub for test_switch.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_setup() -> None:
    """Stub for test_switch_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_guest_wifi_status_auth_failed() -> None:
    """Stub for test_update_guest_wifi_status_auth_failed."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_enable_guest_wifi() -> None:
    """Stub for test_update_enable_guest_wifi."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_enable_leds() -> None:
    """Stub for test_update_enable_leds."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device_failure() -> None:
    """Stub for test_device_failure."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def auth_failed() -> None:
    """Stub for test_auth_failed."""


