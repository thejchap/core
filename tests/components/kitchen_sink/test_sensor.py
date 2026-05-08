"""Tryke skip-stubs for test_sensor.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def states() -> None:
    """Stub for test_states."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def states_with_subentry() -> None:
    """Stub for test_states_with_subentry."""
