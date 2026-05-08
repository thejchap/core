"""Tryke skip-stubs for test_number.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def number_entities() -> None:
    """Stub for test_number_entities."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def entities_not_created_for_device() -> None:
    """Stub for test_entities_not_created_for_device."""
