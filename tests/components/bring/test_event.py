"""Tryke skip stub for test_event.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setup() -> None:
    """Stub for test_setup."""


