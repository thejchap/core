"""Tryke skip stub for test_time.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def times() -> None:
    """Stub for test_times."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def time() -> None:
    """Stub for test_time."""


