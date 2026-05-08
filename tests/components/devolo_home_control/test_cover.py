"""Tryke skip stub for test_cover.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def cover() -> None:
    """Stub for test_cover."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def remove_from_hass() -> None:
    """Stub for test_remove_from_hass."""


