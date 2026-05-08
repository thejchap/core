"""Tryke skip stub for test_button.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def pressing_button() -> None:
    """Stub for test_pressing_button."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def pressing_button_exception() -> None:
    """Stub for test_pressing_button_exception."""


