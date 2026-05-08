"""Tryke skip-stubs for test_number.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def general_numbers() -> None:
    """Stub for test_general_numbers."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def preinfusion() -> None:
    """Stub for test_preinfusion."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def prebrew_on() -> None:
    """Stub for test_prebrew_on."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def prebrew_off() -> None:
    """Stub for test_prebrew_off."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def number_error() -> None:
    """Stub for test_number_error."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def steam_temperature() -> None:
    """Stub for test_steam_temperature."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def brew_by_weight_dose() -> None:
    """Stub for test_brew_by_weight_dose."""
