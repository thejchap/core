"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def buttons() -> None:
    """Stub for test_buttons."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def button_presses() -> None:
    """Stub for test_button_presses."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def buttons_unavailable_on_disconnected_scale() -> None:
    """Stub for test_buttons_unavailable_on_disconnected_scale."""

