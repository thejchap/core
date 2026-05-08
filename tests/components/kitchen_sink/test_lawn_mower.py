"""Tryke skip-stubs for test_lawn_mower.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def states() -> None:
    """Stub for test_states."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def mower() -> None:
    """Stub for test_mower."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def service_calls_mocked() -> None:
    """Stub for test_service_calls_mocked."""
