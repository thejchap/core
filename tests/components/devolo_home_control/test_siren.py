"""Tryke skip stub for test_siren.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def siren() -> None:
    """Stub for test_siren."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def siren_switching() -> None:
    """Stub for test_siren_switching."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def siren_change_default_tone() -> None:
    """Stub for test_siren_change_default_tone."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def remove_from_hass() -> None:
    """Stub for test_remove_from_hass."""


