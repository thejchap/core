"""Tryke skip stub for test_switch.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switches() -> None:
    """Stub for test_switches."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch() -> None:
    """Stub for test_switch."""


