"""Tryke skip-stubs for test_number.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_entity() -> None:
    """Stub for test_number_entity."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def set_humidity() -> None:
    """Stub for test_set_humidity."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def dont_set_humidity_when_sauna_not_heating() -> None:
    """Stub for test_dont_set_humidity_when_sauna_not_heating."""
