"""Tryke skip stub for test_button.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def button_setup() -> None:
    """Stub for test_button_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def button() -> None:
    """Stub for test_button."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def auth_failed() -> None:
    """Stub for test_auth_failed."""


