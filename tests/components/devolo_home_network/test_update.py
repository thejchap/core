"""Tryke skip stub for test_update.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_setup() -> None:
    """Stub for test_update_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_firmware() -> None:
    """Stub for test_update_firmware."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device_failure_check() -> None:
    """Stub for test_device_failure_check."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device_failure_update() -> None:
    """Stub for test_device_failure_update."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def auth_failed() -> None:
    """Stub for test_auth_failed."""


