"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_entities() -> None:
    """Stub for test_button_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_presses() -> None:
    """Stub for test_button_presses."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_press_error() -> None:
    """Stub for test_button_press_error."""

