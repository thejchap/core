"""Tryke skip stub for test_light.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def lights() -> None:
    """Stub for test_lights."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def light() -> None:
    """Stub for test_light."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def light_unknown_state() -> None:
    """Stub for test_light_unknown_state."""


