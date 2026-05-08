"""Tryke skip stub for test_light.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def turn_on() -> None:
    """Stub for test_turn_on."""


