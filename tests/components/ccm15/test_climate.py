"""Tryke skip stub for test_climate.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_state() -> None:
    """Stub for test_climate_state."""


