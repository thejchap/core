"""Tryke skip stub for test_device_tracker.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device_tracker() -> None:
    """Stub for test_device_tracker."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def restoring_clients() -> None:
    """Stub for test_restoring_clients."""


