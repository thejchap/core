"""Tryke skip-stubs for test_light.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def light_attributes_state_update() -> None:
    """Stub for test_light_attributes_state_update."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def light_service_calls() -> None:
    """Stub for test_light_service_calls."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def light_restore_brightness() -> None:
    """Stub for test_light_restore_brightness."""
