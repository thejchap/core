"""Tryke skip-stubs for test_switch.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def entities_not_created_for_device() -> None:
    """Stub for test_entities_not_created_for_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def switch_entities() -> None:
    """Stub for test_switch_entities."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def switch_unreachable() -> None:
    """Stub for test_switch_unreachable."""
