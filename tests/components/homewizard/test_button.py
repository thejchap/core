"""Tryke skip-stubs for test_button.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def identify_button_entity_not_loaded_when_not_available() -> None:
    """Stub for test_identify_button_entity_not_loaded_when_not_available."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def identify_button() -> None:
    """Stub for test_identify_button."""
