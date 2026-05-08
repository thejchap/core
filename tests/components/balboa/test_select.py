"""Tryke skip stub for test_select.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def selects() -> None:
    """Stub for test_selects."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def select() -> None:
    """Stub for test_select."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def selected_option() -> None:
    """Stub for test_selected_option."""


