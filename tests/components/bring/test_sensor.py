"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def list_access_states() -> None:
    """Stub for test_list_access_states."""


