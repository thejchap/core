"""Tryke skip stub for test_device.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device() -> None:
    """Stub for test_device."""


