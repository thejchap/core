"""Tryke skip stub for test_select.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def state() -> None:
    """Stub for test_state."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_hot_water_plus_level() -> None:
    """Stub for test_set_hot_water_plus_level."""


